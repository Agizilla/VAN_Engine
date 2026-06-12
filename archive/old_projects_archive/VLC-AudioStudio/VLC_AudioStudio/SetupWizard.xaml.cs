using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Diagnostics;
using System.IO;

namespace VLCPlayer
{
    public partial class SetupWizard : Window
    {
        private int _currentStep = 0;
        private List<WizardStep> _steps;

        public SetupWizard()
        {
            InitializeComponent();
            InitializeSteps();
            PreviousButton.Click += PreviousButton_Click;
            NextButton.Click += NextButton_Click;
            CloseButton.Click += CloseButton_Click;
            ShowStep(_currentStep);
        }

        private void InitializeSteps()
        {
            _steps = new List<WizardStep>
            {
                // Step 1: Welcome
                new WizardStep
                {
                    Title = "Welcome to Voice Training Setup",
                    Content = CreateWelcomeContent(),
                    AllowPrevious = false
                },
                
                // Step 2: Check Python
                new WizardStep
                {
                    Title = "Step 1: Verify Python Installation",
                    Content = CreatePythonCheckContent(),
                    AllowPrevious = true
                },
                
                // Step 3: Run Setup Script
                new WizardStep
                {
                    Title = "Step 2: Run Setup Script",
                    Content = CreateSetupScriptContent(),
                    AllowPrevious = true
                },
                
                // Step 4: Prepare Audio
                new WizardStep
                {
                    Title = "Step 3: Prepare Training Audio",
                    Content = CreateAudioPrepContent(),
                    AllowPrevious = true
                },
                
                // Step 5: Next Steps
                new WizardStep
                {
                    Title = "Setup Complete!",
                    Content = CreateCompleteContent(),
                    AllowPrevious = true
                }
            };
        }

        private UIElement CreateWelcomeContent()
        {
            var orangeBrush = (Brush)Resources["OrangeBrush"];
            var textBrush = (Brush)Resources["TextFg"];
            var dimBrush = (Brush)Resources["TextDimFg"];

            return new StackPanel
            {
                Children =
                {
                    new TextBlock 
                    { 
                        Text = "Welcome!", 
                        Foreground = orangeBrush, 
                        FontSize = 18, 
                        FontWeight = FontWeights.Bold, 
                        Margin = new Thickness(0, 0, 0, 16) 
                    },
                    new TextBlock 
                    { 
                        Text = "This wizard will help you set up the Voice Training Pipeline in 5 minutes.\n\n" +
                               "✓ Verify Python installation\n" +
                               "✓ Run automatic setup script\n" +
                               "✓ Prepare your training audio\n" +
                               "✓ Start training your first model",
                        Foreground = textBrush,
                        TextWrapping = TextWrapping.Wrap,
                        LineHeight = 28,
                        Margin = new Thickness(0, 0, 0, 20)
                    },
                    new TextBlock 
                    { 
                        Text = "Requirements:\n• Python 3.8+ installed\n• 8GB RAM (16GB recommended)\n• 5-10 audio samples (.wav files)",
                        Foreground = dimBrush,
                        TextWrapping = TextWrapping.Wrap,
                        LineHeight = 20,
                        FontSize = 11
                    }
                }
            };
        }

        private UIElement CreatePythonCheckContent()
        {
            var orangeBrush = (Brush)Resources["OrangeBrush"];
            var textBrush = (Brush)Resources["TextFg"];
            var dimBrush = (Brush)Resources["TextDimFg"];
            
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock 
            { 
                Text = "Checking Python...", 
                Foreground = textBrush,
                FontSize = 14,
                Margin = new Thickness(0, 0, 0, 16)
            });

            bool pythonFound = CheckPython();
            var statusColor = pythonFound ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FF00")) 
                                          : new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF0000"));
            var statusText = pythonFound ? "✓ Python found" : "✗ Python not found";

            panel.Children.Add(new TextBlock 
            { 
                Text = statusText,
                Foreground = statusColor,
                FontSize = 14,
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 20)
            });

            if (pythonFound)
            {
                panel.Children.Add(new TextBlock 
                { 
                    Text = "Great! Python is installed and ready.\n\nClick 'Next >' to continue with the setup script.",
                    Foreground = textBrush,
                    TextWrapping = TextWrapping.Wrap,
                    LineHeight = 24
                });
            }
            else
            {
                panel.Children.Add(new TextBlock 
                { 
                    Text = "Python is not installed or not in PATH.\n\nPlease install Python 3.8+ from:\nhttps://www.python.org/downloads/\n\nMake sure to check 'Add Python to PATH' during installation.",
                    Foreground = textBrush,
                    TextWrapping = TextWrapping.Wrap,
                    LineHeight = 24
                });
            }

            return panel;
        }

        private UIElement CreateSetupScriptContent()
        {
            var textBrush = (Brush)Resources["TextFg"];
            var dimBrush = (Brush)Resources["TextDimFg"];
            var buttonStyle = (Style)Resources["ButtonStyle"];
            
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock 
            { 
                Text = "The setup script will install all Python dependencies (may take 5-10 minutes).",
                Foreground = textBrush,
                TextWrapping = TextWrapping.Wrap,
                LineHeight = 24,
                Margin = new Thickness(0, 0, 0, 20)
            });

            var setupButton = new Button 
            { 
                Content = "▶ Run setup_training.bat",
                Style = buttonStyle,
                Padding = new Thickness(20, 12, 20, 12),
                FontSize = 14,
                Margin = new Thickness(0, 0, 0, 20)
            };
            setupButton.Click += (s, e) => RunSetupScript();
            panel.Children.Add(setupButton);

            panel.Children.Add(new TextBlock 
            { 
                Text = "This will:\n• Create Python virtual environment\n• Install dependencies (40+ packages)\n• Create necessary folders\n• Verify all installations",
                Foreground = dimBrush,
                TextWrapping = TextWrapping.Wrap,
                LineHeight = 24,
                FontSize = 12
            });

            return panel;
        }

        private UIElement CreateAudioPrepContent()
        {
            var orangeBrush = (Brush)Resources["OrangeBrush"];
            var textBrush = (Brush)Resources["TextFg"];
            
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock 
            { 
                Text = "Prepare Your Training Audio",
                Foreground = orangeBrush,
                FontSize = 16,
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 16)
            });

            panel.Children.Add(new TextBlock 
            { 
                Text = "You need 5-10 audio samples of the artist's voice:\n\n" +
                       "✓ Duration: 10-30 seconds each\n" +
                       "✓ Format: .wav (mono or stereo)\n" +
                       "✓ Quality: Clear, minimal background noise\n\n" +
                       "Place files in:\ntraining_data/artist_samples/\n\n" +
                       "Sources:\n• YouTube videos\n• Existing recordings\n• Fresh recordings (recommended)",
                Foreground = textBrush,
                TextWrapping = TextWrapping.Wrap,
                LineHeight = 24
            });

            return panel;
        }

        private UIElement CreateCompleteContent()
        {
            var textBrush = (Brush)Resources["TextFg"];
            var completeBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FF00"));
            
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock 
            { 
                Text = "✅ Setup Complete!",
                Foreground = completeBrush,
                FontSize = 20,
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 20)
            });

            panel.Children.Add(new TextBlock 
            { 
                Text = "You're ready to start training!\n\n" +
                       "Next steps:\n\n" +
                       "1. Open Audio Tools (click button in main window)\n" +
                       "2. Click 'Voice Training' tab\n" +
                       "3. Select your training audio folder\n" +
                       "4. Click 'Start Training'\n\n" +
                       "Training will take 30 min - 4 hours depending on your hardware.",
                Foreground = textBrush,
                TextWrapping = TextWrapping.Wrap,
                LineHeight = 24
            });

            return panel;
        }

        private bool CheckPython()
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
                process.WaitForExit(5000);
                return process.ExitCode == 0;
            }
            catch
            {
                return false;
            }
        }

        private void RunSetupScript()
        {
            try
            {
                var batchFile = Path.Combine(PathHelper.ProjectRoot, "setup_training.bat");
                if (File.Exists(batchFile))
                {
                    Process.Start(batchFile);
                    MessageBox.Show("Setup script started. This will take 5-10 minutes.\n\nA window will open with installation progress.\n\nOnce complete, click 'Next >' to continue.", "Setup Started", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    MessageBox.Show("setup_training.bat not found at: " + batchFile, "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error running setup: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ShowStep(int stepIndex)
        {
            if (stepIndex < 0 || stepIndex >= _steps.Count) return;

            _currentStep = stepIndex;
            var step = _steps[stepIndex];

            StepTitle.Text = step.Title;
            StepProgress.Text = $"Step {stepIndex + 1} of {_steps.Count}";

            ContentPanel.Children.Clear();
            ContentPanel.Children.Add((UIElement)step.Content);

            PreviousButton.IsEnabled = step.AllowPrevious && stepIndex > 0;
            NextButton.IsEnabled = stepIndex < _steps.Count - 1;
            NextButton.Content = stepIndex == _steps.Count - 1 ? "Close" : "Next →";
        }

        private void NextButton_Click(object sender, RoutedEventArgs e)
        {
            if (_currentStep < _steps.Count - 1)
                ShowStep(_currentStep + 1);
            else
                Close();
        }

        private void PreviousButton_Click(object sender, RoutedEventArgs e)
        {
            if (_currentStep > 0)
                ShowStep(_currentStep - 1);
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private class WizardStep
        {
            public string Title { get; set; }
            public object Content { get; set; }
            public bool AllowPrevious { get; set; }
        }
    }
}

