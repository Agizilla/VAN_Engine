using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace VLCPlayer
{
    /// <summary>
    /// Service for managing artist lexicon (unique tokens/words from lyrics)
    /// </summary>
    public class LexiconService
    {
        /// <summary>
        /// Get all unique tokens (words) from an artist's lyrics
        /// </summary>
        public static HashSet<string> GetArtistTokens(string artistName)
        {
            var tokens = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var lyricsFolder = PathHelper.GetArtistLyricsFolder(artistName);

            if (!Directory.Exists(lyricsFolder))
                return tokens;

            try
            {
                // Get all text files from lyrics folder
                var lyricFiles = Directory.GetFiles(lyricsFolder, "*.txt");

                foreach (var file in lyricFiles)
                {
                    try
                    {
                        var content = File.ReadAllText(file);
                        var words = ExtractTokens(content);

                        foreach (var word in words)
                        {
                            tokens.Add(word);
                        }
                    }
                    catch
                    {
                        // Skip files that can't be read
                    }
                }
            }
            catch
            {
                // Skip if folder can't be accessed
            }

            return tokens;
        }

        /// <summary>
        /// Extract tokens (words) from text
        /// Converts to lowercase and removes punctuation
        /// </summary>
        private static List<string> ExtractTokens(string text)
        {
            var tokens = new List<string>();

            if (string.IsNullOrWhiteSpace(text))
                return tokens;

            // Remove punctuation and split by whitespace
            var cleaned = Regex.Replace(text, @"[^\w\s]", " ");
            var words = cleaned.Split(new[] { ' ', '\n', '\r', '\t' }, StringSplitOptions.RemoveEmptyEntries);

            foreach (var word in words)
            {
                var lowerWord = word.ToLower().Trim();
                if (lowerWord.Length > 1) // Ignore single characters
                {
                    tokens.Add(lowerWord);
                }
            }

            return tokens;
        }

        /// <summary>
        /// Get trained tokens (from training config or database)
        /// For now, reads from a trained_tokens.txt file in the artist folder
        /// </summary>
        public static HashSet<string> GetTrainedTokens(string artistName)
        {
            var tokens = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var trainedTokensFile = PathHelper.GetAbsolutePath($"trained_tokens/{artistName}_trained.txt");

            if (File.Exists(trainedTokensFile))
            {
                try
                {
                    var content = File.ReadAllText(trainedTokensFile);
                    var lines = content.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

                    foreach (var line in lines)
                    {
                        var token = line.Trim();
                        if (!string.IsNullOrWhiteSpace(token))
                        {
                            tokens.Add(token);
                        }
                    }
                }
                catch
                {
                    // If file can't be read, return empty set
                }
            }

            return tokens;
        }

        /// <summary>
        /// Save trained tokens for an artist
        /// </summary>
        public static void SaveTrainedTokens(string artistName, IEnumerable<string> tokens)
        {
            try
            {
                var folder = PathHelper.GetAbsolutePath("trained_tokens");
                if (!Directory.Exists(folder))
                {
                    Directory.CreateDirectory(folder);
                }

                var filePath = Path.Combine(folder, $"{artistName}_trained.txt");
                var content = string.Join(Environment.NewLine, tokens.OrderBy(t => t));

                File.WriteAllText(filePath, content);
            }
            catch
            {
                // Silently fail if can't save
            }
        }

        /// <summary>
        /// Get untrained tokens (all tokens minus trained tokens)
        /// </summary>
        public static HashSet<string> GetUntrainedTokens(string artistName)
        {
            var allTokens = GetArtistTokens(artistName);
            var trainedTokens = GetTrainedTokens(artistName);

            allTokens.ExceptWith(trainedTokens);
            return allTokens;
        }

        /// <summary>
        /// Get statistics about lexicon coverage
        /// </summary>
        public static (int Total, int Trained, int Untrained, double Percentage) GetCoverageStats(string artistName)
        {
            var allTokens = GetArtistTokens(artistName);
            var trainedTokens = GetTrainedTokens(artistName);

            var total = allTokens.Count;
            var trained = trainedTokens.Count;
            var untrained = total - trained;
            var percentage = total > 0 ? (trained * 100.0) / total : 0;

            return (total, trained, untrained, percentage);
        }

        /// <summary>
        /// Mark token as trained
        /// </summary>
        public static void MarkTokenTrained(string artistName, string token)
        {
            var trainedTokens = GetTrainedTokens(artistName);
            trainedTokens.Add(token);
            SaveTrainedTokens(artistName, trainedTokens);
        }

        /// <summary>
        /// Mark token as untrained
        /// </summary>
        public static void MarkTokenUntrained(string artistName, string token)
        {
            var trainedTokens = GetTrainedTokens(artistName);
            trainedTokens.Remove(token);
            SaveTrainedTokens(artistName, trainedTokens);
        }
    }
}
