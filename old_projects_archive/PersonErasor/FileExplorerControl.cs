using System.Drawing;
using System.Windows.Forms;
using SovereignIDE.Core.Models;

namespace SovereignIDE.UI.Controls;

public class FileExplorerControl : UserControl
{
    private TreeView _treeView;
    private TextBox _searchBox;
    private Label _headerLabel;

    public event EventHandler<FileEntry>? FileSelected;

    public FileExplorerControl()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        BackColor = Color.FromArgb(15, 15, 15);

        // Header
        _headerLabel = new Label
        {
            Text = "PROJECT FILES",
            Dock = DockStyle.Top,
            Height = 40,
            BackColor = Color.FromArgb(10, 10, 10),
            ForeColor = Color.FromArgb(180, 180, 180),
            Font = new Font("Segoe UI", 10, FontStyle.Bold),
            Padding = new Padding(10, 0, 0, 0),
            TextAlign = ContentAlignment.MiddleLeft
        };

        // Search box
        _searchBox = new TextBox
        {
            Dock = DockStyle.Top,
            Height = 30,
            BackColor = Color.FromArgb(25, 25, 25),
            ForeColor = Color.FromArgb(200, 200, 200),
            BorderStyle = BorderStyle.FixedSingle,
            Font = new Font("Consolas", 10),
            PlaceholderText = "Search files..."
        };

        // Tree view
        _treeView = new TreeView
        {
            Dock = DockStyle.Fill,
            BackColor = Color.FromArgb(15, 15, 15),
            ForeColor = Color.FromArgb(220, 220, 220),
            BorderStyle = BorderStyle.None,
            Font = new Font("Consolas", 9),
            HideSelection = false
        };

        _treeView.NodeMouseDoubleClick += OnNodeDoubleClick;

        Controls.Add(_treeView);
        Controls.Add(_searchBox);
        Controls.Add(_headerLabel);
    }

    public void LoadFiles(List<FileEntry> files)
    {
        _treeView.Nodes.Clear();

        var root = new TreeNode("Project")
        {
            Tag = null
        };

        foreach (var file in files)
        {
            AddFileNode(root, file);
        }

        root.Expand();
        _treeView.Nodes.Add(root);
    }

    private void AddFileNode(TreeNode parent, FileEntry file)
    {
        var parts = file.Path.Split('/');
        var current = parent;

        for (int i = 0; i < parts.Length - 1; i++)
        {
            var existing = current.Nodes.Cast<TreeNode>()
                .FirstOrDefault(n => n.Text == parts[i]);

            if (existing == null)
            {
                existing = new TreeNode(parts[i]);
                current.Nodes.Add(existing);
            }

            current = existing;
        }

        var fileName = parts[^1];
        var fileNode = new TreeNode(fileName)
        {
            Tag = file,
            ForeColor = file.State switch
            {
                FileState.Created => Color.FromArgb(100, 200, 100),
                FileState.Modified => Color.FromArgb(200, 150, 100),
                FileState.Deleted => Color.FromArgb(200, 100, 100),
                _ => Color.FromArgb(220, 220, 220)
            }
        };

        current.Nodes.Add(fileNode);
    }

    private void OnNodeDoubleClick(object? sender, TreeNodeMouseClickEventArgs e)
    {
        if (e.Node.Tag is FileEntry file)
        {
            FileSelected?.Invoke(this, file);
        }
    }
}
