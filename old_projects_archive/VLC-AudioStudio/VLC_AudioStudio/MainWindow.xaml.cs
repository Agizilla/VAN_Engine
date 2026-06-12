using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using NAudio.Wave;
using Microsoft.Win32;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Diagnostics;

namespace VLCPlayer
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private IWavePlayer _wavePlayer;
        private AudioFileReader _audioFileReader;
        private DispatcherTimer _timer;
        private string _currentFilePath;
        private bool _isPlaying = false;

        public MainWindow()
        {
            InitializeComponent();
            InitializePlayer();
            AttachEventHandlers();
            InitializeVoiceTrainingHandlers();
            
            // Hook up any missing button handlers after loading
            this.Loaded += MainWindow_Loaded;
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            // Try to attach Song Training button if it exists
            try
            {
                var songButton = this.FindName("SongTrainingButton") as System.Windows.Controls.Button;
                if (songButton != null)
                {
                    songButton.Click += SongTrainingButton_Click;
                }
                
                var quickTrainButton = this.FindName("QuickTrainButton") as System.Windows.Controls.Button;
                if (quickTrainButton != null)
                {
                    quickTrainButton.Click += QuickTrainButton_Click;
                }
            }
            catch { }
        }

        private void InitializePlayer()
        {
            _wavePlayer = new WaveOutEvent();
            _timer = new DispatcherTimer();
            _timer.Interval = TimeSpan.FromMilliseconds(500);
            _timer.Tick += Timer_Tick;
        }

        private void AttachEventHandlers()
        {
            OpenFileButton.Click += OpenFileButton_Click;
            PlayPauseButton.Click += PlayPauseButton_Click;
            StopButton.Click += StopButton_Click;
            NextButton.Click += NextButton_Click;
            PreviousButton.Click += PreviousButton_Click;
            VolumeSlider.ValueChanged += VolumeSlider_ValueChanged;
            AudioToolsButton.Click += AudioToolsButton_Click;
            
            // Wizard buttons - safely attach if they exist
            if (SetupWizardButton != null)
                SetupWizardButton.Click += SetupWizardButton_Click;
                
            if (TrainingGuideButton != null)
                TrainingGuideButton.Click += TrainingGuideButton_Click;
                
            if (QuickstartButton != null)
                QuickstartButton.Click += QuickstartButton_Click;
        }

        private void SetupWizardButton_Click(object sender, RoutedEventArgs e)
        {
            var wizard = new SetupWizard { Owner = this };
            wizard.ShowDialog();
        }

        private void TrainingGuideButton_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "📖 TRAINING GUIDE\n\n" +
                "Complete technical documentation:\n\n" +
                "• Detailed configuration\n" +
                "• Advanced usage\n" +
                "• Troubleshooting\n" +
                "• Best practices\n\n" +
                "See: TRAINING_GUIDE.md in project root",
                "Training Guide",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void QuickstartButton_Click(object sender, RoutedEventArgs e)
        {
            var wizard = new TrainingQuickstartWizard { Owner = this };
            wizard.ShowDialog();
        }

        private void SongTrainingButton_Click(object sender, RoutedEventArgs e)
        {
            var wizard = new SongTrainingWizard { Owner = this };
            wizard.ShowDialog();
        }

        private void QuickTrainButton_Click(object sender, RoutedEventArgs e)
        {
            // Quick Train opens the Song Training Wizard
            var wizard = new SongTrainingWizard { Owner = this };
            wizard.ShowDialog();
        }

        private void OpenFileButton_Click(object sender, RoutedEventArgs e)
        {
            OpenFileDialog openFileDialog = new OpenFileDialog();
            openFileDialog.Filter = "Audio Files (*.mp3;*.wav;*.flac;*.aac)|*.mp3;*.wav;*.flac;*.aac|Video Files (*.mp4;*.mkv;*.avi)|*.mp4;*.mkv;*.avi|All Files (*.*)|*.*";
            
            if (openFileDialog.ShowDialog() == true)
            {
                LoadAudioFile(openFileDialog.FileName);
            }
        }

        private void LoadAudioFile(string filePath)
        {
            try
            {
                // Stop current playback
                _wavePlayer?.Stop();
                _audioFileReader?.Dispose();

                // Load new file
                _currentFilePath = filePath;
                _audioFileReader = new AudioFileReader(filePath);
                _wavePlayer.Init(_audioFileReader);

                // Update UI
                string fileName = System.IO.Path.GetFileName(filePath);
                CurrentTrackLabel.Text = $"Now loaded: {fileName}";
                MediaViewerPlaceholder.Visibility = Visibility.Visible;
                AudioToolsPanel.Visibility = Visibility.Collapsed;

                // Update time display
                TotalTimeLabel.Text = FormatTime(_audioFileReader.TotalTime);
                CurrentTimeLabel.Text = "00:00";

                // Reset play button
                PlayPauseButton.Content = "▶️";
                _isPlaying = false;

                _timer.Stop();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error loading file: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void PlayPauseButton_Click(object sender, RoutedEventArgs e)
        {
            if (_audioFileReader == null)
            {
                MessageBox.Show("Please load an audio file first.", "No File Loaded", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            if (_isPlaying)
            {
                _wavePlayer.Pause();
                PlayPauseButton.Content = "▶️";
                _timer.Stop();
                _isPlaying = false;
            }
            else
            {
                _wavePlayer.Play();
                PlayPauseButton.Content = "⏸️";
                _timer.Start();
                _isPlaying = true;
            }
        }

        private void StopButton_Click(object sender, RoutedEventArgs e)
        {
            if (_wavePlayer != null)
            {
                _wavePlayer.Stop();
                _audioFileReader?.Seek(0, System.IO.SeekOrigin.Begin);
                CurrentTimeLabel.Text = "00:00";
                PlayPauseButton.Content = "▶️";
                _isPlaying = false;
                _timer.Stop();
            }
        }

        private void NextButton_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Next button functionality would load next track in playlist.", "Info", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void PreviousButton_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Previous button functionality would load previous track in playlist.", "Info", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void VolumeSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (_audioFileReader != null)
            {
                _audioFileReader.Volume = (float)(e.NewValue / 100.0);
            }
        }

        private void Timer_Tick(object sender, EventArgs e)
        {
            if (_audioFileReader != null && _wavePlayer.PlaybackState == PlaybackState.Playing)
            {
                CurrentTimeLabel.Text = FormatTime(_audioFileReader.CurrentTime);
                
                // Update progress bar
                double progressPercentage = (_audioFileReader.CurrentTime.TotalSeconds / _audioFileReader.TotalTime.TotalSeconds) * 100;
                ProgressBar.Width = (ProgressBar.Parent as Grid)?.ActualWidth * (progressPercentage / 100) ?? 0;

                // Check if song ended
                if (_audioFileReader.CurrentTime >= _audioFileReader.TotalTime)
                {
                    StopButton_Click(null, null);
                }
            }
        }

        private void AudioToolsButton_Click(object sender, RoutedEventArgs e)
        {
            if (_audioFileReader == null)
            {
                MessageBox.Show("Please load an audio track first to use Audio Tools.", "No Track Loaded", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            // Toggle between media viewer and audio tools
            if (MediaViewerPlaceholder.Visibility == Visibility.Visible)
            {
                MediaViewerPlaceholder.Visibility = Visibility.Collapsed;
                AudioToolsPanel.Visibility = Visibility.Visible;
            }
            else
            {
                MediaViewerPlaceholder.Visibility = Visibility.Visible;
                AudioToolsPanel.Visibility = Visibility.Collapsed;
            }
        }

        private string FormatTime(TimeSpan timeSpan)
        {
            return $"{(int)timeSpan.TotalMinutes:D2}:{timeSpan.Seconds:D2}";
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);
            _wavePlayer?.Dispose();
            _audioFileReader?.Dispose();
            _timer?.Stop();
        }
    }
}
