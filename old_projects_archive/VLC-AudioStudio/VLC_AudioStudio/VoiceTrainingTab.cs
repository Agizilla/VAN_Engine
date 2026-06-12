using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.IO;
using System.Linq;
using Microsoft.Win32;

namespace VLCPlayer
{
    /// <summary>
    /// Partial class containing Voice Training Tab logic
    /// </summary>
    public partial class MainWindow : Window
    {
        private List<string> _selectedTrainingFiles = new List<string>();
        private string _trainingFolder = "";
        private string _whisperModel = "";

        /// <summary>
        /// Initialize Voice Training Tab handlers
        /// </summary>
        public void InitializeVoiceTrainingHandlers()
        {
            try
            {
                // Find and attach handlers
                var browseTrainingButton = this.FindName("BrowseTrainingFolderButton") as System.Windows.Controls.Button;
                if (browseTrainingButton != null)
                    browseTrainingButton.Click += BrowseTrainingFolder_Click;

                var browseWhisperButton = this.FindName("BrowseWhisperModelButton") as System.Windows.Controls.Button;
                if (browseWhisperButton != null)
                    browseWhisperButton.Click += BrowseWhisperModel_Click;

                var refreshButton = this.FindName("RefreshFilesButton") as System.Windows.Controls.Button;
                if (refreshButton != null)
                    refreshButton.Click += RefreshFiles_Click;

                var validateButton = this.FindName("ValidateDataButton") as System.Windows.Controls.Button;
                if (validateButton != null)
                    validateButton.Click += ValidateData_Click;

                var startButton = this.FindName("StartTrainingButton") as System.Windows.Controls.Button;
                if (startButton != null)
                    startButton.Click += StartTraining_Click;
            }
            catch { }
        }

        /// <summary>
        /// Browse for training folder
        /// </summary>
        private void BrowseTrainingFolder_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new System.Windows.Forms.FolderBrowserDialog
            {
                Description = "Select training audio folder",
                SelectedPath = PathHelper.ArtistSamplesFolder
            };

            if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
            {
                _trainingFolder = dialog.SelectedPath;
                var folderBox = this.FindName("TrainingAudioFolderBox") as System.Windows.Controls.TextBox;
                if (folderBox != null)
                    folderBox.Text = _trainingFolder;

                LoadTrainingFiles();
                ValidateInputs();
            }
        }

        /// <summary>
        /// Browse for Whisper model file
        /// </summary>
        private void BrowseWhisperModel_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Filter = "Model Files (*.pth,*.pt,*.bin)|*.pth;*.pt;*.bin|All Files (*.*)|*.*",
                InitialDirectory = PathHelper.ModelsFolder,
                Title = "Select Whisper Model"
            };

            if (dialog.ShowDialog() == true)
            {
                _whisperModel = dialog.FileName;
                var dropdown = this.FindName("WhisperModelDropdown") as System.Windows.Controls.ComboBox;
                if (dropdown != null)
                {
                    dropdown.Items.Clear();
                    dropdown.Items.Add(Path.GetFileName(_whisperModel));
                    dropdown.SelectedIndex = 0;
                }
                ValidateInputs();
            }
        }

        /// <summary>
        /// Load training files from folder
        /// </summary>
        private void LoadTrainingFiles()
        {
            var panel = this.FindName("TrainingFilesPanel") as StackPanel;
            if (panel == null || string.IsNullOrEmpty(_trainingFolder)) return;

            panel.Children.Clear();
            _selectedTrainingFiles.Clear();

            try
            {
                var wavFiles = Directory.GetFiles(_trainingFolder, "*.wav")
                    .Concat(Directory.GetFiles(_trainingFolder, "*.mp3"))
                    .Concat(Directory.GetFiles(_trainingFolder, "*.flac"))
                    .Concat(Directory.GetFiles(_trainingFolder, "*.aac"))
                    .ToArray();

                if (wavFiles.Length == 0)
                {
                    panel.Children.Add(new TextBlock
                    {
                        Text = "(No audio files found in folder)",
                        Foreground = (System.Windows.Media.Brush)Resources["TextDimFg"],
                        Margin = new Thickness(4)
                    });
                    return;
                }

                foreach (var file in wavFiles)
                {
                    var fileInfo = new FileInfo(file);
                    var checkbox = new System.Windows.Controls.CheckBox
                    {
                        Content = $"{Path.GetFileName(file)} ({fileInfo.Length / (1024 * 1024):F1} MB)",
                        Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                        Margin = new Thickness(4, 2, 4, 2),
                        IsChecked = false,
                        Tag = file
                    };

                    checkbox.Checked += (s, e) =>
                    {
                        if (!_selectedTrainingFiles.Contains(file))
                            _selectedTrainingFiles.Add(file);
                        ValidateInputs();
                    };

                    checkbox.Unchecked += (s, e) =>
                    {
                        _selectedTrainingFiles.Remove(file);
                        ValidateInputs();
                    };

                    panel.Children.Add(checkbox);
                }

                UpdateSampleCount();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading training files: {ex.Message}");
            }
        }

        /// <summary>
        /// Refresh files list
        /// </summary>
        private void RefreshFiles_Click(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(_trainingFolder))
                LoadTrainingFiles();
        }

        /// <summary>
        /// Validate all inputs and enable/disable Start Training button
        /// </summary>
        private void ValidateInputs()
        {
            var isValid = true;
            var messages = new List<string>();

            // Check project name
            var projectNameBox = this.FindName("ProjectNameBox") as System.Windows.Controls.TextBox;
            if (projectNameBox == null || string.IsNullOrWhiteSpace(projectNameBox.Text))
            {
                isValid = false;
                messages.Add("✗ Project name required");
            }
            else
            {
                messages.Add("✓ Project name set");
            }

            // Check training folder
            if (string.IsNullOrEmpty(_trainingFolder))
            {
                isValid = false;
                messages.Add("✗ Training folder not selected");
            }
            else
            {
                messages.Add("✓ Training folder selected");
            }

            // Check selected files
            if (_selectedTrainingFiles.Count == 0)
            {
                isValid = false;
                messages.Add("✗ No training files selected");
            }
            else
            {
                messages.Add($"✓ {_selectedTrainingFiles.Count} file(s) selected");
            }

            // Check sample length
            var sampleLengthBox = this.FindName("SampleLengthBox") as System.Windows.Controls.TextBox;
            if (sampleLengthBox == null || !int.TryParse(sampleLengthBox.Text, out int sampleLength) || sampleLength <= 0)
            {
                isValid = false;
                messages.Add("✗ Invalid sample length");
            }
            else
            {
                messages.Add($"✓ Sample length: {sampleLength}s");
            }

            // Check whisper model
            if (string.IsNullOrEmpty(_whisperModel))
            {
                isValid = false;
                messages.Add("✗ Whisper model not selected");
            }
            else
            {
                messages.Add($"✓ Model: {Path.GetFileName(_whisperModel)}");
            }

            // Update status label
            var statusLabel = this.FindName("TrainingStatusLabel") as TextBlock;
            if (statusLabel != null)
            {
                statusLabel.Text = isValid ? "✓ Ready to train" : "⚠ Configure required fields";
                statusLabel.Foreground = isValid ? 
                    new System.Windows.Media.SolidColorBrush(System.Windows.Media.Colors.LimeGreen) :
                    new System.Windows.Media.SolidColorBrush(System.Windows.Media.Colors.Orange);
            }

            // Enable/disable Start Training button
            var startButton = this.FindName("StartTrainingButton") as System.Windows.Controls.Button;
            if (startButton != null)
                startButton.IsEnabled = isValid;

            // Log validation messages
            var logBox = this.FindName("TrainingLogBox") as System.Windows.Controls.TextBox;
            if (logBox != null)
            {
                logBox.Text = string.Join("\n", messages) + "\n\n" + logBox.Text;
            }
        }

        /// <summary>
        /// Validate data - manual button click
        /// </summary>
        private void ValidateData_Click(object sender, RoutedEventArgs e)
        {
            ValidateInputs();
            MessageBox.Show(
                _selectedTrainingFiles.Count > 0 ? 
                    $"✓ Validation successful!\n\n{_selectedTrainingFiles.Count} file(s) ready for training." :
                    "✗ Validation failed. Please configure all required fields.",
                "Validation Result",
                MessageBoxButton.OK,
                _selectedTrainingFiles.Count > 0 ? MessageBoxImage.Information : MessageBoxImage.Warning);
        }

        /// <summary>
        /// Start training
        /// </summary>
        private void StartTraining_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedTrainingFiles.Count == 0)
            {
                MessageBox.Show("No training files selected!", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            var projectNameBox = this.FindName("ProjectNameBox") as System.Windows.Controls.TextBox;
            var projectName = projectNameBox?.Text ?? "training";

            var sampleLengthBox = this.FindName("SampleLengthBox") as System.Windows.Controls.TextBox;
            var sampleLength = 10;
            if (int.TryParse(sampleLengthBox?.Text, out int length))
                sampleLength = length;

            MessageBox.Show(
                $"Training Configuration:\n\n" +
                $"Project: {projectName}\n" +
                $"Files: {_selectedTrainingFiles.Count}\n" +
                $"Sample Length: {sampleLength}s\n" +
                $"Whisper Model: {Path.GetFileName(_whisperModel)}\n\n" +
                $"Training will begin in a new window.",
                "Start Training",
                MessageBoxButton.OK,
                MessageBoxImage.Information);

            // TODO: Implement actual training logic
            var logBox = this.FindName("TrainingLogBox") as System.Windows.Controls.TextBox;
            if (logBox != null)
            {
                logBox.Text = $"[{DateTime.Now:HH:mm:ss}] Starting training...\n" +
                              $"[{DateTime.Now:HH:mm:ss}] Project: {projectName}\n" +
                              $"[{DateTime.Now:HH:mm:ss}] Files: {_selectedTrainingFiles.Count}\n" +
                              $"[{DateTime.Now:HH:mm:ss}] Sample length: {sampleLength}s\n\n" +
                              logBox.Text;
            }
        }

        /// <summary>
        /// Update sample count display
        /// </summary>
        private void UpdateSampleCount()
        {
            var sampleCountLabel = this.FindName("SampleCountLabel") as TextBlock;
            if (sampleCountLabel != null)
            {
                sampleCountLabel.Text = _selectedTrainingFiles.Count == 0 ? 
                    "0 files selected" : 
                    $"{_selectedTrainingFiles.Count} file(s) selected";
            }
        }
    }
}
