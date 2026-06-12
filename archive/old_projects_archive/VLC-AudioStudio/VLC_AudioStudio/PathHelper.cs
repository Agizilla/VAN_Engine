using System;
using System.IO;
using System.Reflection;

namespace VLCPlayer
{
    /// <summary>
    /// Utility class for managing project-relative paths
    /// Ensures paths are based on project root, not bin folder
    /// </summary>
    public static class PathHelper
    {
        private static string _projectRoot;

        /// <summary>
        /// Get the project root directory
        /// </summary>
        public static string ProjectRoot
        {
            get
            {
                if (string.IsNullOrEmpty(_projectRoot))
                {
                    // Get the directory where the executable is running
                    var assembly = Assembly.GetExecutingAssembly();
                    var codeBase = assembly.CodeBase;
                    var uri = new UriBuilder(codeBase);
                    var path = Uri.UnescapeDataString(uri.Path);
                    var binDirectory = Path.GetDirectoryName(path);

                    // Go up from bin/Debug/net6.0-windows to project root
                    _projectRoot = Directory.GetParent(binDirectory)?.Parent?.Parent?.FullName;

                    // If that doesn't work, try alternative method
                    if (string.IsNullOrEmpty(_projectRoot) || !Directory.Exists(_projectRoot))
                    {
                        _projectRoot = AppDomain.CurrentDomain.BaseDirectory;
                        // Remove bin folder from path
                        while (_projectRoot.EndsWith("bin") || _projectRoot.EndsWith("bin\\") || _projectRoot.EndsWith("bin/"))
                        {
                            _projectRoot = Path.GetDirectoryName(_projectRoot);
                        }
                    }
                }
                return _projectRoot;
            }
        }

        /// <summary>
        /// Get absolute path from relative path
        /// </summary>
        public static string GetAbsolutePath(string relativePath)
        {
            if (Path.IsPathRooted(relativePath))
                return relativePath;

            return Path.Combine(ProjectRoot, relativePath);
        }

        /// <summary>
        /// Get training data folder path
        /// </summary>
        public static string TrainingDataFolder => GetAbsolutePath("training_data");

        /// <summary>
        /// Get artist samples folder path
        /// </summary>
        public static string ArtistSamplesFolder => GetAbsolutePath("training_data/artist_samples");

        /// <summary>
        /// Get trained models folder path
        /// </summary>
        public static string TrainedModelsFolder => GetAbsolutePath("trained_models");

        /// <summary>
        /// Get Python scripts folder path
        /// </summary>
        public static string PythonScriptsFolder => GetAbsolutePath("python_scripts");

        /// <summary>
        /// Get song configs folder path
        /// </summary>
        public static string SongConfigsFolder => GetAbsolutePath("song_configs");

        /// <summary>
        /// Get lyrics folder path for a specific artist
        /// </summary>
        public static string GetArtistLyricsFolder(string artistName)
        {
            return GetAbsolutePath($"lyrics/{artistName}");
        }

        /// <summary>
        /// Get models folder path
        /// </summary>
        public static string ModelsFolder => GetAbsolutePath("models");

        /// <summary>
        /// Ensure directory exists
        /// </summary>
        public static void EnsureDirectoryExists(string path)
        {
            var absolutePath = GetAbsolutePath(path);
            if (!Directory.Exists(absolutePath))
            {
                Directory.CreateDirectory(absolutePath);
            }
        }

        /// <summary>
        /// Get all artist folders from training_data/artist_samples
        /// </summary>
        public static string[] GetArtistFolders()
        {
            try
            {
                var samplesFolder = ArtistSamplesFolder;
                if (!Directory.Exists(samplesFolder))
                {
                    return Array.Empty<string>();
                }

                var directories = Directory.GetDirectories(samplesFolder);
                var artistNames = new string[directories.Length];

                for (int i = 0; i < directories.Length; i++)
                {
                    artistNames[i] = Path.GetFileName(directories[i]);
                }

                return artistNames;
            }
            catch
            {
                return Array.Empty<string>();
            }
        }

        /// <summary>
        /// Get all trained models
        /// </summary>
        public static string[] GetTrainedModels()
        {
            try
            {
                var modelsFolder = TrainedModelsFolder;
                if (!Directory.Exists(modelsFolder))
                {
                    return Array.Empty<string>();
                }

                var directories = Directory.GetDirectories(modelsFolder);
                var modelNames = new string[directories.Length];

                for (int i = 0; i < directories.Length; i++)
                {
                    modelNames[i] = Path.GetFileName(directories[i]);
                }

                return modelNames;
            }
            catch
            {
                return Array.Empty<string>();
            }
        }
    }
}
