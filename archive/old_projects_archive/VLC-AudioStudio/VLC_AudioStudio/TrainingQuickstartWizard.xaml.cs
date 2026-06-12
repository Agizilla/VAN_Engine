using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;

namespace VLCPlayer
{
    public partial class TrainingQuickstartWizard : Window
    {
        private int _currentStep = 0;
        private List<Step> _steps;

        public TrainingQuickstartWizard()
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
            _steps = new List<Step>
            {
                new Step 
                { 
                    Title = "Voice Training in 5 Minutes", 
                    Content = "✓ Setup wizard completed\n✓ Audio samples prepared\n✓ Ready to train\n\nThis guide shows you exactly what to do next to train your first voice model."
                },
                new Step 
                { 
                    Title = "Start Training", 
                    Content = "1. Click the 'Audio Tools' button in the main window\n\n2. Look for the 'Voice Training' tab\n\n3. The training UI will show:\n   • Project name\n   • Training folder\n   • Training parameters\n   • Status display\n   • Training log"
                },
                new Step 
                { 
                    Title = "Training Parameters", 
                    Content = "Default values are optimized for most cases:\n\n" +
                              "Epochs: 100\n   → Higher = better quality but slower\n\n" +
                              "Batch Size: 4\n   → Standard for 8GB RAM\n\n" +
                              "Learning Rate: 0.0001\n   → Don't change unless needed\n\n" +
                              "Whisper Model: base\n   → Recommended for singing"
                },
                new Step 
                { 
                    Title = "Run Training", 
                    Content = "1. Click 'Browse Samples' → Select training_data/artist_samples\n\n2. Click 'Validate Data' → Should show sample count\n\n3. Review the parameters\n\n4. Click '🚀 Start Training'\n\n5. Watch progress in the log window\n\nExpected times:\n• GPU: 30-60 minutes\n• CPU: 2-4 hours"
                },
                new Step 
                { 
                    Title = "After Training", 
                    Content = "When training completes:\n\n✅ Model saved to: trained_models/\n\n✅ Training results logged\n\n✅ Ready to clone voices\n\nTo use your trained model:\n\n1. Open an audio file\n\n2. Click 'Voice Cloning' tab\n\n3. Select your trained model\n\n4. Click 'Clone Voice'\n\n5. Output saved as: file_cloned.wav"
                }
            };
        }

        private void ShowStep(int index)
        {
            if (index < 0 || index >= _steps.Count) return;
            
            _currentStep = index;
            var step = _steps[index];

            StepTitle.Text = step.Title;
            StepProgress.Text = $"Step {index + 1} of {_steps.Count}";
            ContentText.Text = step.Content;

            PreviousButton.IsEnabled = index > 0;
            NextButton.IsEnabled = index < _steps.Count - 1;
        }

        private void NextButton_Click(object sender, RoutedEventArgs e) => ShowStep(_currentStep + 1);
        private void PreviousButton_Click(object sender, RoutedEventArgs e) => ShowStep(_currentStep - 1);
        private void CloseButton_Click(object sender, RoutedEventArgs e) => Close();

        private class Step 
        { 
            public string Title { get; set; } 
            public string Content { get; set; } 
        }
    }
}
