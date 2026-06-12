// VLC_AudioStudio Voice Model Training Integration
// Add this code to MainWindow.xaml.cs

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;

namespace VLCPlayer
{
    /// <summary>
    /// Voice model training functionality
    /// </summary>
    public partial class MainWindow : Window
    {
        // Training-related fields
        private bool _isTraining = false;
        private Process _trainingProcess;
        private string _trainingDataFolder = PathHelper.ArtistSamplesFolder;
        private string _trainedModelsFolder = PathHelper.TrainedModelsFolder;

        /// <summary>
        /// Initialize training UI event handlers
        /// NOTE: This is now handled by VoiceTrainingTab.cs
        /// </summary>
        private void InitializeTrainingHandlers()
        {
            try
            {
                // Handlers are now initialized by InitializeVoiceTrainingHandlers() in VoiceTrainingTab.cs
                // This method is kept for backward compatibility but not called
                
                /*
                if (BrowseTrainingDataButton != null)
                    BrowseTrainingDataButton.Click += BrowseTrainingDataButton_Click;

                if (ValidateDataButton != null)
                    ValidateDataButton.Click += ValidateDataButton_Click;

                if (StartTrainingButton != null)
                    StartTrainingButton.Click += StartTrainingButton_Click;
                */

                // Initialize training folders
                Directory.CreateDirectory(_trainingDataFolder);
                Directory.CreateDirectory(_trainedModelsFolder);

                UpdateTrainingStatus("Ready");
                CountTrainingFiles();
            }
            catch (Exception ex)
            {
                LogTrainingMessage($"Error initializing training: {ex.Message}");
            }
        }

        /// <summary>
        /// Browse for training audio files
        /// NOTE: This is now handled by VoiceTrainingTab.cs BrowseTrainingFolder_Click
        /// </summary>
        /*
        private void BrowseTrainingDataButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new System.Windows.Forms.FolderBrowserDialog();
            dialog.Description = "Select folder with training audio files (.wav)";
            dialog.SelectedPath = _trainingDataFolder;

            if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
            {
                _trainingDataFolder = dialog.SelectedPath;
                LogTrainingMessage($"Training folder set to: {_trainingDataFolder}");
                CountTrainingFiles();
            }
        }
        */

        /// <summary>
        /// Validate training data
        /// </summary>
        /// <summary>
        /// Validate training data
        /// NOTE: This is now handled by VoiceTrainingTab.cs ValidateData_Click
        /// </summary>
        /*
        private void ValidateDataButton_Click(object sender, RoutedEventArgs e)
        {
            LogTrainingMessage("Validating training data...");
            CountTrainingFiles();

            var wavFiles = Directory.GetFiles(_trainingDataFolder, "*.wav");

            if (wavFiles.Length == 0)
            {
                LogTrainingMessage("❌ No .wav files found in training folder!");
                return;
            }

            LogTrainingMessage($"✓ Found {wavFiles.Length} audio files");

            // Validate each file
            foreach (var file in wavFiles)
            {
                try
                {
                    var info = new FileInfo(file);
                    LogTrainingMessage($"  • {Path.GetFileName(file)} ({info.Length / 1024 / 1024:F1}MB)");
                }
                catch { }
            }

            LogTrainingMessage("✓ Data validation complete!");
            MessageBox.Show($"Found {wavFiles.Length} training samples. Ready to train!");
        }
        */

        /// <summary>
        /// Count and display available training files
        /// </summary>
        private void CountTrainingFiles()
        {
            try
            {
                if (!Directory.Exists(_trainingDataFolder))
                {
                    SampleCountLabel.Text = "0 found";
                    return;
                }

                var wavFiles = Directory.GetFiles(_trainingDataFolder, "*.wav").Length;
                SampleCountLabel.Text = $"{wavFiles} found";
            }
            catch
            {
                SampleCountLabel.Text = "Error counting";
            }
        }

        /// <summary>
        /// Start training the voice model
        /// </summary>
        private async void StartTrainingButton_Click(object sender, RoutedEventArgs e)
        {
            if (_isTraining)
            {
                StopTraining();
                return;
            }

            // Validate data
            var wavFiles = Directory.GetFiles(_trainingDataFolder, "*.wav");
            if (wavFiles.Length == 0)
            {
                MessageBox.Show("No training audio files found! Please add .wav files to the training folder.", "No Data", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (wavFiles.Length < 3)
            {
                MessageBox.Show("Minimum 3 training samples recommended. Found: " + wavFiles.Length, "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
            }

            _isTraining = true;
            StartTrainingButton.Content = "⏹️ Stop Training";
            UpdateTrainingStatus("Training in progress...");
            LogTrainingMessage($"Starting training with {wavFiles.Length} samples...");

            await Task.Run(() => RunTrainingPipeline());
        }

        /// <summary>
        /// Run the Python training pipeline
        /// </summary>
        private void RunTrainingPipeline()
        {
            try
            {
                // Check if Python is available
                if (!IsPythonAvailable())
                {
                    Dispatcher.Invoke(() =>
                    {
                        LogTrainingMessage("❌ Python not found! Please install Python or run setup_training.bat");
                        MessageBox.Show("Python is not installed or not in PATH. Please run setup_training.bat first.");
                        StopTraining();
                    });
                    return;
                }

                // Create training config
                var config = CreateTrainingConfig();
                var configPath = Path.Combine(Directory.GetCurrentDirectory(), "training_config_temp.json");

                File.WriteAllText(configPath, JsonSerializer.Serialize(config, new JsonSerializerOptions { WriteIndented = true }));

                Dispatcher.Invoke(() =>
                {
                    LogTrainingMessage("Training configuration created");
                });

                // Launch Python training script
                var pythonScriptPath = Path.Combine(PathHelper.PythonScriptsFolder, "train_voice_model.py");

                if (!File.Exists(pythonScriptPath))
                {
                    Dispatcher.Invoke(() =>
                    {
                        LogTrainingMessage($"❌ Python script not found: {pythonScriptPath}");
                        StopTraining();
                    });
                    return;
                }

                _trainingProcess = new Process();
                _trainingProcess.StartInfo.FileName = "python";
                _trainingProcess.StartInfo.Arguments = $"\"{pythonScriptPath}\" --config \"{configPath}\"";
                _trainingProcess.StartInfo.UseShellExecute = false;
                _trainingProcess.StartInfo.RedirectStandardOutput = true;
                _trainingProcess.StartInfo.RedirectStandardError = true;
                _trainingProcess.StartInfo.CreateNoWindow = true;

                _trainingProcess.OutputDataReceived += (s, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        Dispatcher.Invoke(() => LogTrainingMessage(e.Data));
                    }
                };

                _trainingProcess.ErrorDataReceived += (s, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        Dispatcher.Invoke(() => LogTrainingMessage($"Error: {e.Data}"));
                    }
                };

                Dispatcher.Invoke(() =>
                {
                    LogTrainingMessage("Launching Python training process...");
                });

                _trainingProcess.Start();
                _trainingProcess.BeginOutputReadLine();
                _trainingProcess.BeginErrorReadLine();

                _trainingProcess.WaitForExit();

                // Training completed
                Dispatcher.Invoke(() =>
                {
                    if (_trainingProcess.ExitCode == 0)
                    {
                        LogTrainingMessage("✅ Training completed successfully!");
                        UpdateTrainingStatus("Completed");
                        MessageBox.Show("Training completed! Your voice model is ready to use.");
                    }
                    else
                    {
                        LogTrainingMessage($"❌ Training failed with exit code {_trainingProcess.ExitCode}");
                        UpdateTrainingStatus("Failed");
                    }

                    StopTraining();
                });

                // Clean up temp config
                File.Delete(configPath);
            }
            catch (Exception ex)
            {
                Dispatcher.Invoke(() =>
                {
                    LogTrainingMessage($"❌ Training error: {ex.Message}");
                    UpdateTrainingStatus("Error");
                    StopTraining();
                });
            }
        }

        /// <summary>
        /// Check if Python is available
        /// </summary>
        private bool IsPythonAvailable()
        {
            try
            {
                var process = new Process();
                process.StartInfo.FileName = "python";
                process.StartInfo.Arguments = "--version";
                process.StartInfo.UseShellExecute = false;
                process.StartInfo.RedirectStandardOutput = true;
                process.StartInfo.CreateNoWindow = true;

                process.Start();
                var version = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                LogTrainingMessage($"Python found: {version.Trim()}");
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Create training configuration
        /// </summary>
        private Dictionary<string, object> CreateTrainingConfig()
        {
            return new Dictionary<string, object>
            {
                { "project_name", "VLC_AudioStudio Voice Model" },
                { "training_audio_folder", _trainingDataFolder },
                { "output_folder", _trainedModelsFolder },
                { "num_epochs", 100 },
                { "batch_size", 4 },
                { "learning_rate", 0.0001 },
                { "validation_split", 0.1 },
                { "sample_rate", 24000 },
                { "whisper_model", "base" },
                { "device", "cuda" },
                { "use_mixed_precision", true },
                { "checkpoint_interval", 10 }
            };
        }

        /// <summary>
        /// Stop training
        /// </summary>
        private void StopTraining()
        {
            _isTraining = false;
            if (_trainingProcess != null && !_trainingProcess.HasExited)
            {
                _trainingProcess.Kill();
            }

            StartTrainingButton.Content = "🚀 Start Training";
            UpdateTrainingStatus("Stopped");
        }

        /// <summary>
        /// Log a message to the training log box
        /// </summary>
        private void LogTrainingMessage(string message)
        {
            try
            {
                var timestamp = DateTime.Now.ToString("HH:mm:ss");
                var logMessage = $"[{timestamp}] {message}\n";

                TrainingLogBox.AppendText(logMessage);
                TrainingLogBox.ScrollToEnd();

                // Limit log size
                if (TrainingLogBox.Text.Length > 50000)
                {
                    TrainingLogBox.Text = TrainingLogBox.Text.Substring(TrainingLogBox.Text.Length - 25000);
                }
            }
            catch { }
        }

        /// <summary>
        /// Update training status display
        /// </summary>
        private void UpdateTrainingStatus(string status)
        {
            try
            {
                var statusColor = status == "Ready" ? "{StaticResource OrangeBrush}" :
                                 status == "Training in progress..." ? "{StaticResource OrangeBrush}" :
                                 status == "Completed" ? "#00FF00" :
                                 status == "Failed" ? "#FF0000" : "#B3B3B3";

                // Update via label if available (simplified approach)
                // In real implementation, bind to a ViewModel property
            }
            catch { }
        }

        /// <summary>
        /// Clone voice using trained model
        /// </summary>
        public async Task<string> CloneVoiceWithTrainedModel(
            string inputAudio,
            string modelPath,
            int pitchShift = 0)
        {
            try
            {
                var pythonScript = Path.Combine(Directory.GetCurrentDirectory(), "python_scripts", "infer_voice_model.py");

                var process = new Process();
                process.StartInfo.FileName = "python";
                process.StartInfo.Arguments = $"\"{pythonScript}\" --model \"{modelPath}\" --input \"{inputAudio}\" --pitch-shift {pitchShift}";
                process.StartInfo.UseShellExecute = false;
                process.StartInfo.RedirectStandardOutput = true;
                process.StartInfo.CreateNoWindow = true;

                process.Start();
                var output = await process.StandardOutput.ReadToEndAsync();
                process.WaitForExit();

                if (process.ExitCode == 0 && !string.IsNullOrEmpty(output))
                {
                    var outputPath = output.Trim();
                    if (File.Exists(outputPath))
                    {
                        return outputPath;
                    }
                }

                return null;
            }
            catch (Exception ex)
            {
                LogTrainingMessage($"Voice cloning error: {ex.Message}");
                return null;
            }
        }
    }
}
