using System.Drawing;
using System.Windows.Forms;
using SovereignIDE.Core.Execution;
using SovereignIDE.Core.Models;

namespace SovereignIDE.UI.Controls;

public class CommandQueueControl : UserControl
{
    private ListView _listView;
    private Label _headerLabel;
    private Button _approveAllButton;
    private Button _clearButton;
    private CommandQueue? _commandQueue;

    public event EventHandler<CommandEntry>? CommandApproved;
    public event EventHandler<CommandEntry>? CommandRejected;
    public event EventHandler<CommandEntry>? ExecuteCommand;

    public CommandQueueControl()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        BackColor = Color.FromArgb(15, 15, 15);

        // Header
        var headerPanel = new Panel
        {
            Dock = DockStyle.Top,
            Height = 40,
            BackColor = Color.FromArgb(10, 10, 10)
        };

        _headerLabel = new Label
        {
            Text = "COMMAND QUEUE",
            Location = new Point(10, 10),
            Size = new Size(200, 20),
            ForeColor = Color.FromArgb(180, 180, 180),
            Font = new Font("Segoe UI", 10, FontStyle.Bold)
        };

        _clearButton = new Button
        {
            Text = "Clear",
            Location = new Point(headerPanel.Width - 80, 5),
            Size = new Size(70, 30),
            Anchor = AnchorStyles.Top | AnchorStyles.Right,
            BackColor = Color.FromArgb(60, 60, 60),
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat
        };
        _clearButton.Click += (s, e) => _commandQueue?.ClearCompleted();

        headerPanel.Controls.Add(_headerLabel);
        headerPanel.Controls.Add(_clearButton);

        // List view
        _listView = new ListView
        {
            Dock = DockStyle.Fill,
            View = View.Details,
            FullRowSelect = true,
            BackColor = Color.FromArgb(20, 20, 20),
            ForeColor = Color.FromArgb(220, 220, 220),
            BorderStyle = BorderStyle.None,
            Font = new Font("Consolas", 9)
        };

        _listView.Columns.Add("Command", 300);
        _listView.Columns.Add("Type", 80);
        _listView.Columns.Add("Status", 80);

        _listView.MouseDoubleClick += OnListViewDoubleClick;

        Controls.Add(_listView);
        Controls.Add(headerPanel);
    }

    public void SetCommandQueue(CommandQueue commandQueue)
    {
        _commandQueue = commandQueue;

        _commandQueue.CommandAdded += (s, e) => RefreshList();
        _commandQueue.CommandApproved += (s, e) => RefreshList();
        _commandQueue.CommandRejected += (s, e) => RefreshList();
        _commandQueue.CommandExecuted += (s, e) => RefreshList();
    }

    private void RefreshList()
    {
        if (_commandQueue == null)
            return;

        _listView.Items.Clear();

        foreach (var command in _commandQueue.All)
        {
            var item = new ListViewItem(command.Command);
            item.SubItems.Add(command.Type.ToString());
            item.SubItems.Add(command.Status.ToString());
            item.Tag = command;

            // Color coding
            item.ForeColor = command.Status switch
            {
                CommandStatus.Pending => Color.FromArgb(200, 200, 100),
                CommandStatus.Approved => Color.FromArgb(100, 200, 100),
                CommandStatus.Executed => Color.FromArgb(150, 150, 150),
                CommandStatus.Failed => Color.FromArgb(200, 100, 100),
                CommandStatus.Rejected => Color.FromArgb(150, 100, 100),
                _ => Color.FromArgb(220, 220, 220)
            };

            _listView.Items.Add(item);
        }

        _headerLabel.Text = $"COMMAND QUEUE ({_commandQueue.Pending.Count} pending)";
    }

    private void OnListViewDoubleClick(object? sender, MouseEventArgs e)
    {
        if (_listView.SelectedItems.Count == 0)
            return;

        var command = _listView.SelectedItems[0].Tag as CommandEntry;
        if (command == null)
            return;

        if (command.Status == CommandStatus.Pending)
        {
            ShowApprovalDialog(command);
        }
    }

    private void ShowApprovalDialog(CommandEntry command)
    {
        var result = MessageBox.Show(
            $"Execute this command?\n\n{command.Command}\n\nType: {command.Type}\nDangerous: {command.RequiresApproval}",
            "Approve Command",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Question
        );

        if (result == DialogResult.Yes)
        {
            CommandApproved?.Invoke(this, command);
        }
        else
        {
            CommandRejected?.Invoke(this, command);
        }
    }
}
