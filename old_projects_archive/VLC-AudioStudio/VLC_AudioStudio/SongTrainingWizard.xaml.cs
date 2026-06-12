using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.IO;
using Microsoft.Win32;

namespace VLCPlayer
{
    public partial class SongTrainingWizard : Window
    {
        private int _currentStep = 0;
        private List<TrainStep> _steps;
        
        // Step data
        private string _selectedVocalsFile;
        private string _selectedBaseModel;
        private string _selectedWhisperConfig;
        private int _sampleLength = 10; // seconds
        private string _lyrics = "";
        private Dictionary<string, double> _settings = new Dictionary<string, double>();
        private string _testWords = "";

        public SongTrainingWizard()
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
            _steps = new List<TrainStep>
            {
                // Step 1: Select Song Vocals
                new TrainStep
                {
                    Title = "Step 1: Select Song Vocals",
                    Content = CreateSelectVocalsContent(),
                    AllowPrevious = false
                },
                
                // Step 2: Choose Base Model
                new TrainStep
                {
                    Title = "Step 2: Choose Base Model",
                    Content = CreateChooseModelContent(),
                    AllowPrevious = true
                },
                
                // Step 3: Whisper Configuration
                new TrainStep
                {
                    Title = "Step 3: Whisper Configuration",
                    Content = CreateWhisperConfigContent(),
                    AllowPrevious = true
                },
                
                // Step 4: Train
                new TrainStep
                {
                    Title = "Step 4: Train Song",
                    Content = CreateTrainContent(),
                    AllowPrevious = true
                },
                
                // Step 5: Preview
                new TrainStep
                {
                    Title = "Step 5: Preview & Adjust",
                    Content = CreatePreviewContent(),
                    AllowPrevious = true
                },
                
                // Step 6: Test
                new TrainStep
                {
                    Title = "Step 6: Test Results",
                    Content = CreateTestContent(),
                    AllowPrevious = true
                },
                
                // Step 7: Save
                new TrainStep
                {
                    Title = "Step 7: Save Model",
                    Content = CreateSaveContent(),
                    AllowPrevious = true
                }
            };
        }

        private UIElement CreateSelectVocalsContent()
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock
            {
                Text = "Select the song vocals (*.wav file)",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 16),
                LineHeight = 24
            });

            var fileGrid = new Grid { Margin = new Thickness(0, 0, 0, 16) };
            fileGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            fileGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var fileTextBox = new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                Padding = new Thickness(8),
                Height = 32,
                IsReadOnly = true,
                Text = _selectedVocalsFile ?? "(no file selected)"
            };
            Grid.SetColumn(fileTextBox, 0);
            fileGrid.Children.Add(fileTextBox);

            var browseButton = new Button
            {
                Content = "📁 Browse",
                Style = (Style)Resources["ButtonStyle"],
                Margin = new Thickness(8, 0, 0, 0),
                Padding = new Thickness(12, 8, 12, 8)
            };
            browseButton.Click += (s, e) =>
            {
                var dialog = new OpenFileDialog
                {
                    Filter = "WAV Files (*.wav)|*.wav|All Files (*.*)|*.*",
                    InitialDirectory = PathHelper.ProjectRoot,
                    Title = "Select Song Vocals"
                };

                if (dialog.ShowDialog() == true)
                {
                    _selectedVocalsFile = dialog.FileName;
                    fileTextBox.Text = Path.GetFileName(_selectedVocalsFile);
                }
            };
            Grid.SetColumn(browseButton, 1);
            fileGrid.Children.Add(browseButton);

            panel.Children.Add(fileGrid);

            if (!string.IsNullOrEmpty(_selectedVocalsFile))
            {
                panel.Children.Add(new TextBlock
                {
                    Text = $"✓ Selected: {Path.GetFileName(_selectedVocalsFile)}",
                    Foreground = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Colors.LimeGreen),
                    FontWeight = FontWeights.Bold,
                    Margin = new Thickness(0, 16, 0, 0)
                });
            }

            return panel;
        }

        private UIElement CreateChooseModelContent()
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock
            {
                Text = "Select base model (*.pth file)",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 16)
            });

            var modelGrid = new Grid { Margin = new Thickness(0, 0, 0, 16) };
            modelGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            modelGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var modelTextBox = new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                Padding = new Thickness(8),
                Height = 32,
                IsReadOnly = true,
                Text = _selectedBaseModel ?? "(no model selected)"
            };
            Grid.SetColumn(modelTextBox, 0);
            modelGrid.Children.Add(modelTextBox);

            var browseButton = new Button
            {
                Content = "📁 Browse",
                Style = (Style)Resources["ButtonStyle"],
                Margin = new Thickness(8, 0, 0, 0),
                Padding = new Thickness(12, 8, 12, 8)
            };
            browseButton.Click += (s, e) =>
            {
                var dialog = new OpenFileDialog
                {
                    Filter = "PyTorch Models (*.pth)|*.pth|All Files (*.*)|*.*",
                    InitialDirectory = PathHelper.ModelsFolder,
                    Title = "Select Base Model"
                };

                if (dialog.ShowDialog() == true)
                {
                    _selectedBaseModel = dialog.FileName;
                    modelTextBox.Text = Path.GetFileName(_selectedBaseModel);
                }
            };
            Grid.SetColumn(browseButton, 1);
            modelGrid.Children.Add(browseButton);

            panel.Children.Add(modelGrid);

            if (!string.IsNullOrEmpty(_selectedBaseModel))
            {
                panel.Children.Add(new TextBlock
                {
                    Text = $"✓ Selected: {Path.GetFileName(_selectedBaseModel)}",
                    Foreground = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Colors.LimeGreen),
                    FontWeight = FontWeights.Bold,
                    Margin = new Thickness(0, 16, 0, 0)
                });
            }

            return panel;
        }

        private UIElement CreateWhisperConfigContent()
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock
            {
                Text = "Whisper Configuration (optional)",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 16)
            });

            var configGrid = new Grid { Margin = new Thickness(0, 0, 0, 16) };
            configGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            configGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var configTextBox = new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                Padding = new Thickness(8),
                Height = 32,
                IsReadOnly = true,
                Text = _selectedWhisperConfig ?? "(auto-generate)"
            };
            Grid.SetColumn(configTextBox, 0);
            configGrid.Children.Add(configTextBox);

            var browseButton = new Button
            {
                Content = "📁 Browse",
                Style = (Style)Resources["ButtonStyle"],
                Margin = new Thickness(8, 0, 0, 0),
                Padding = new Thickness(12, 8, 12, 8)
            };
            browseButton.Click += (s, e) =>
            {
                var dialog = new OpenFileDialog
                {
                    Filter = "JSON Config (*.json)|*.json|All Files (*.*)|*.*",
                    InitialDirectory = PathHelper.SongConfigsFolder,
                    Title = "Select Whisper Config"
                };

                if (dialog.ShowDialog() == true)
                {
                    _selectedWhisperConfig = dialog.FileName;
                    configTextBox.Text = Path.GetFileName(_selectedWhisperConfig);
                }
            };
            Grid.SetColumn(browseButton, 1);
            configGrid.Children.Add(browseButton);

            panel.Children.Add(configGrid);

            panel.Children.Add(new TextBlock
            {
                Text = "If no config is selected, Whisper will be used to generate one automatically",
                Foreground = (System.Windows.Media.Brush)Resources["TextDimFg"],
                FontSize = 11,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 8, 0, 0)
            });

            return panel;
        }

        private UIElement CreateTrainContent()
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock
            {
                Text = "Configure training parameters",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 16)
            });

            panel.Children.Add(new TextBlock
            {
                Text = "Sample Length (seconds):",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 8)
            });

            var lengthSlider = new Slider
            {
                Minimum = 5,
                Maximum = 30,
                Value = _sampleLength,
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["OrangeBrush"],
                Margin = new Thickness(0, 0, 0, 4)
            };
            panel.Children.Add(lengthSlider);

            var valueLabel = new TextBlock
            {
                Text = $"{_sampleLength} seconds",
                Foreground = (System.Windows.Media.Brush)Resources["TextDimFg"],
                Margin = new Thickness(0, 0, 0, 16)
            };
            lengthSlider.ValueChanged += (s, e) =>
            {
                _sampleLength = (int)e.NewValue;
                valueLabel.Text = $"{_sampleLength} seconds";
            };
            panel.Children.Add(valueLabel);

            panel.Children.Add(new Border
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                BorderBrush = (System.Windows.Media.Brush)Resources["ButtonHoverBg"],
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(12),
                Margin = new Thickness(0, 0, 0, 16),
                Child = new StackPanel
                {
                    Children =
                    {
                        new TextBlock
                        {
                            Text = "⚙️ Audio will be sliced into multiple samples of the selected length",
                            Foreground = (System.Windows.Media.Brush)Resources["TextDimFg"],
                            TextWrapping = TextWrapping.Wrap,
                            Margin = new Thickness(0, 0, 0, 8)
                        },
                        new TextBlock
                        {
                            Text = "Training may take 10 minutes to several hours depending on your hardware",
                            Foreground = (System.Windows.Media.Brush)Resources["TextDimFg"],
                            TextWrapping = TextWrapping.Wrap
                        }
                    }
                }
            });

            panel.Children.Add(new Button
            {
                Content = "▶ Start Training",
                Style = (Style)Resources["ButtonStyle"],
                Padding = new Thickness(20, 12, 20, 12),
                FontSize = 14,
                Margin = new Thickness(0, 0, 0, 0)
            });

            return panel;
        }

        private UIElement CreatePreviewContent()
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock
            {
                Text = "Preview and adjust training results",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 16)
            });

            panel.Children.Add(new TextBlock
            {
                Text = "Lyrics:",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 8)
            });

            var lyricsBox = new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                Padding = new Thickness(8),
                Height = 120,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                TextWrapping = TextWrapping.Wrap,
                AcceptsReturn = true,
                Text = _lyrics,
                Margin = new Thickness(0, 0, 0, 16)
            };
            lyricsBox.TextChanged += (s, e) => _lyrics = lyricsBox.Text;
            panel.Children.Add(lyricsBox);

            panel.Children.Add(new TextBlock
            {
                Text = "Adjustment Settings:",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 8)
            });

            var settingsBox = new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextDimFg"],
                Padding = new Thickness(8),
                Height = 100,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                TextWrapping = TextWrapping.Wrap,
                Text = "Pitch: 0\nTempo: 1.0\nVolume: 1.0",
                Margin = new Thickness(0, 0, 0, 16)
            };
            panel.Children.Add(settingsBox);

            panel.Children.Add(new Button
            {
                Content = "⟲ Reload with Adjustments",
                Style = (Style)Resources["ButtonStyle"],
                Padding = new Thickness(20, 12, 20, 12)
            });

            return panel;
        }

        private UIElement CreateTestContent()
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock
            {
                Text = "Test the trained model with new words",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 16)
            });

            panel.Children.Add(new TextBlock
            {
                Text = "Test Words:",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 8)
            });

            var testBox = new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                Padding = new Thickness(8),
                Height = 120,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                TextWrapping = TextWrapping.Wrap,
                AcceptsReturn = true,
                Text = _testWords,
                Margin = new Thickness(0, 0, 0, 16)
            };
            testBox.TextChanged += (s, e) => _testWords = testBox.Text;
            panel.Children.Add(testBox);

            panel.Children.Add(new Button
            {
                Content = "▶ Test Model",
                Style = (Style)Resources["ButtonStyle"],
                Padding = new Thickness(20, 12, 20, 12)
            });

            return panel;
        }

        private UIElement CreateSaveContent()
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock
            {
                Text = "Save the trained model",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 16)
            });

            panel.Children.Add(new TextBlock
            {
                Text = "Model Name:",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 8)
            });

            panel.Children.Add(new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                Padding = new Thickness(8),
                Height = 32,
                Text = "trained_model",
                Margin = new Thickness(0, 0, 0, 16)
            });

            panel.Children.Add(new TextBlock
            {
                Text = "Save Location:",
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 8)
            });

            var saveGrid = new Grid { Margin = new Thickness(0, 0, 0, 16) };
            saveGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            saveGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var saveTextBox = new TextBox
            {
                Background = (System.Windows.Media.Brush)Resources["ControlBg"],
                Foreground = (System.Windows.Media.Brush)Resources["TextFg"],
                Padding = new Thickness(8),
                Height = 32,
                IsReadOnly = true,
                Text = PathHelper.TrainedModelsFolder
            };
            Grid.SetColumn(saveTextBox, 0);
            saveGrid.Children.Add(saveTextBox);

            var browseButton = new Button
            {
                Content = "📁 Browse",
                Style = (Style)Resources["ButtonStyle"],
                Margin = new Thickness(8, 0, 0, 0),
                Padding = new Thickness(12, 8, 12, 8)
            };
            browseButton.Click += (s, e) =>
            {
                var dialog = new System.Windows.Forms.FolderBrowserDialog
                {
                    Description = "Select save location",
                    SelectedPath = PathHelper.TrainedModelsFolder
                };

                if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                {
                    saveTextBox.Text = dialog.SelectedPath;
                }
            };
            Grid.SetColumn(browseButton, 1);
            saveGrid.Children.Add(browseButton);

            panel.Children.Add(saveGrid);

            panel.Children.Add(new Button
            {
                Content = "💾 Save Model",
                Style = (Style)Resources["ButtonStyle"],
                Padding = new Thickness(20, 12, 20, 12),
                Margin = new Thickness(0, 20, 0, 0)
            });

            return panel;
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

        private class TrainStep
        {
            public string Title { get; set; }
            public object Content { get; set; }
            public bool AllowPrevious { get; set; }
        }
    }
}
