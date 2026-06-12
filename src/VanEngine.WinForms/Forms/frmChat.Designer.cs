namespace VanEngine.WinForms.Forms
{
    partial class frmChat
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            pnlLeft = new Panel();
            pnlServer = new Panel();
            txtIncomingMessage = new RichTextBox();
            panel7 = new Panel();
            btnRunCommands = new Button();
            btnImplementCode = new Button();
            btnSpeakServerMessage = new Button();
            pnlRight = new Panel();
            pnlBottom = new Panel();
            pnlTop = new Panel();
            btnConnectGateway = new Button();
            pnlClient = new Panel();
            txtOutgoingMessage = new RichTextBox();
            panel8 = new Panel();
            btnRecord = new Button();
            btnSpeakClientMessage = new Button();
            splitter1 = new Splitter();
            pnlServer.SuspendLayout();
            panel7.SuspendLayout();
            pnlTop.SuspendLayout();
            pnlClient.SuspendLayout();
            panel8.SuspendLayout();
            SuspendLayout();
            // 
            // pnlLeft
            // 
            pnlLeft.Dock = DockStyle.Left;
            pnlLeft.Location = new Point(0, 34);
            pnlLeft.Name = "pnlLeft";
            pnlLeft.Size = new Size(122, 414);
            pnlLeft.TabIndex = 0;
            // 
            // pnlServer
            // 
            pnlServer.BorderStyle = BorderStyle.FixedSingle;
            pnlServer.Controls.Add(txtIncomingMessage);
            pnlServer.Controls.Add(panel7);
            pnlServer.Dock = DockStyle.Bottom;
            pnlServer.Location = new Point(122, 36);
            pnlServer.Name = "pnlServer";
            pnlServer.Size = new Size(722, 221);
            pnlServer.TabIndex = 1;
            // 
            // txtIncomingMessage
            // 
            txtIncomingMessage.BorderStyle = BorderStyle.None;
            txtIncomingMessage.Dock = DockStyle.Fill;
            txtIncomingMessage.Location = new Point(0, 0);
            txtIncomingMessage.Name = "txtIncomingMessage";
            txtIncomingMessage.Size = new Size(720, 194);
            txtIncomingMessage.TabIndex = 7;
            txtIncomingMessage.Text = "";
            // 
            // panel7
            // 
            panel7.Controls.Add(btnRunCommands);
            panel7.Controls.Add(btnImplementCode);
            panel7.Controls.Add(btnSpeakServerMessage);
            panel7.Dock = DockStyle.Bottom;
            panel7.Location = new Point(0, 194);
            panel7.Name = "panel7";
            panel7.Size = new Size(720, 25);
            panel7.TabIndex = 6;
            // 
            // btnRunCommands
            // 
            btnRunCommands.Dock = DockStyle.Right;
            btnRunCommands.Location = new Point(423, 0);
            btnRunCommands.Name = "btnRunCommands";
            btnRunCommands.Size = new Size(106, 25);
            btnRunCommands.TabIndex = 5;
            btnRunCommands.Text = "Run Commands";
            btnRunCommands.UseVisualStyleBackColor = true;
            // 
            // btnImplementCode
            // 
            btnImplementCode.Dock = DockStyle.Right;
            btnImplementCode.Location = new Point(529, 0);
            btnImplementCode.Name = "btnImplementCode";
            btnImplementCode.Size = new Size(106, 25);
            btnImplementCode.TabIndex = 4;
            btnImplementCode.Text = "Implement Code";
            btnImplementCode.UseVisualStyleBackColor = true;
            // 
            // btnSpeakServerMessage
            // 
            btnSpeakServerMessage.Dock = DockStyle.Right;
            btnSpeakServerMessage.Location = new Point(635, 0);
            btnSpeakServerMessage.Name = "btnSpeakServerMessage";
            btnSpeakServerMessage.Size = new Size(85, 25);
            btnSpeakServerMessage.TabIndex = 3;
            btnSpeakServerMessage.Text = "Speak";
            btnSpeakServerMessage.UseVisualStyleBackColor = true;
            // 
            // pnlRight
            // 
            pnlRight.Dock = DockStyle.Right;
            pnlRight.Location = new Point(844, 34);
            pnlRight.Name = "pnlRight";
            pnlRight.Size = new Size(122, 414);
            pnlRight.TabIndex = 2;
            // 
            // pnlBottom
            // 
            pnlBottom.Dock = DockStyle.Bottom;
            pnlBottom.Location = new Point(0, 448);
            pnlBottom.Name = "pnlBottom";
            pnlBottom.Size = new Size(966, 28);
            pnlBottom.TabIndex = 3;
            // 
            // pnlTop
            // 
            pnlTop.Controls.Add(btnConnectGateway);
            pnlTop.Dock = DockStyle.Top;
            pnlTop.Location = new Point(0, 0);
            pnlTop.Name = "pnlTop";
            pnlTop.Size = new Size(966, 34);
            pnlTop.TabIndex = 4;
            // 
            // btnConnectGateway
            // 
            btnConnectGateway.Dock = DockStyle.Left;
            btnConnectGateway.Location = new Point(0, 0);
            btnConnectGateway.Name = "btnConnectGateway";
            btnConnectGateway.Size = new Size(122, 34);
            btnConnectGateway.TabIndex = 6;
            btnConnectGateway.Text = "Connect Gateway";
            btnConnectGateway.UseVisualStyleBackColor = true;
            // 
            // pnlClient
            // 
            pnlClient.BorderStyle = BorderStyle.FixedSingle;
            pnlClient.Controls.Add(txtOutgoingMessage);
            pnlClient.Controls.Add(panel8);
            pnlClient.Dock = DockStyle.Bottom;
            pnlClient.Location = new Point(122, 260);
            pnlClient.Name = "pnlClient";
            pnlClient.Size = new Size(722, 188);
            pnlClient.TabIndex = 5;
            // 
            // txtOutgoingMessage
            // 
            txtOutgoingMessage.BorderStyle = BorderStyle.None;
            txtOutgoingMessage.Dock = DockStyle.Fill;
            txtOutgoingMessage.Location = new Point(0, 0);
            txtOutgoingMessage.Name = "txtOutgoingMessage";
            txtOutgoingMessage.Size = new Size(720, 161);
            txtOutgoingMessage.TabIndex = 7;
            txtOutgoingMessage.Text = "";
            // 
            // panel8
            // 
            panel8.Controls.Add(btnRecord);
            panel8.Controls.Add(btnSpeakClientMessage);
            panel8.Dock = DockStyle.Bottom;
            panel8.Location = new Point(0, 161);
            panel8.Name = "panel8";
            panel8.Size = new Size(720, 25);
            panel8.TabIndex = 6;
            // 
            // btnRecord
            // 
            btnRecord.Dock = DockStyle.Right;
            btnRecord.Location = new Point(550, 0);
            btnRecord.Name = "btnRecord";
            btnRecord.Size = new Size(85, 25);
            btnRecord.TabIndex = 1;
            btnRecord.Text = "Record";
            btnRecord.UseVisualStyleBackColor = true;
            // 
            // btnSpeakClientMessage
            // 
            btnSpeakClientMessage.Dock = DockStyle.Right;
            btnSpeakClientMessage.Location = new Point(635, 0);
            btnSpeakClientMessage.Name = "btnSpeakClientMessage";
            btnSpeakClientMessage.Size = new Size(85, 25);
            btnSpeakClientMessage.TabIndex = 0;
            btnSpeakClientMessage.Text = "Speak";
            btnSpeakClientMessage.UseVisualStyleBackColor = true;
            // 
            // splitter1
            // 
            splitter1.Dock = DockStyle.Bottom;
            splitter1.Location = new Point(122, 257);
            splitter1.Name = "splitter1";
            splitter1.Size = new Size(722, 3);
            splitter1.TabIndex = 6;
            splitter1.TabStop = false;
            // 
            // frmChat
            // 
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(966, 476);
            Controls.Add(pnlServer);
            Controls.Add(splitter1);
            Controls.Add(pnlClient);
            Controls.Add(pnlRight);
            Controls.Add(pnlLeft);
            Controls.Add(pnlTop);
            Controls.Add(pnlBottom);
            Name = "frmChat";
            Text = "frmChat";
            pnlServer.ResumeLayout(false);
            panel7.ResumeLayout(false);
            pnlTop.ResumeLayout(false);
            pnlClient.ResumeLayout(false);
            panel8.ResumeLayout(false);
            ResumeLayout(false);
        }

        #endregion

        private Panel pnlLeft;
        private Panel pnlServer;
        private Panel pnlRight;
        private Panel pnlBottom;
        private Panel pnlTop;
        private RichTextBox txtIncomingMessage;
        private Panel panel7;
        private Panel pnlClient;
        private RichTextBox txtOutgoingMessage;
        private Panel panel8;
        private Splitter splitter1;
        private Button btnRunCommands;
        private Button btnImplementCode;
        private Button btnSpeakServerMessage;
        private Button button3;
        private Button button2;
        private Button btnSpeakClientMessage;
        private Button btnConnectGateway;
        private Button btnRecord;
    }
}