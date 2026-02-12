import * as vscode from 'vscode';
import * as http from 'http';

export class ContextSidebarProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'contextSyncView';
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
    ) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        // Initial "Welcome" State
        this.showWelcome();

        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(message => {
            if (message.command === 'sync') {
                this.triggerSync();
            } else if (message.command === 'copy') {
                vscode.env.clipboard.writeText(message.text);
                vscode.window.showInformationMessage('Copied to clipboard!');
            }
        });
    }

    public showWelcome() {
        if (this._view) {
            const welcomeHtml = `
                <div class="welcome-container">
                    <div class="icon">🔍</div>
                    <h2>ContextSync</h2>
                    <p>Highlight code and run <b>ContextSync: Explain Intent</b> to reveal key insights.</p>
                </div>
            `;
            this._view.webview.html = this._getHtmlForWebview(welcomeHtml);
        }
    }

    public showLoading() {
        if (this._view) {
            const loadingHtml = `
                <div class="loader-container">
                    <div class="spinner"></div>
                    <p>Analyzing Context...</p>
                </div>
            `;
            this._view.webview.html = this._getHtmlForWebview(loadingHtml);
        }
    }

    public explainCode(codeSnippet: string, filePath: string, lineNumbers: string) {
        const postData = JSON.stringify({
            code_snippet: codeSnippet,
            file_path: filePath,
            line_numbers: lineNumbers
        });

        const options = {
            hostname: '127.0.0.1',
            port: 8000,
            path: '/explain',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                if (res.statusCode === 200) {
                    try {
                        const response = JSON.parse(data);
                        this.updateContent(response.markdown);
                    } catch (e) {
                        this.showError("Failed to parse response.");
                    }
                } else {
                    this.showError(`Error: Server returned ${res.statusCode}`);
                }
            });
        });

        req.on('error', (e) => {
            this.showError("Context Engine Disconnected. Is the Python server running?");
        });

        req.write(postData);
        req.end();
    }

    public fetchContextObjects(codeSnippet: string, filePath: string, lineNumbers: string) {
        const postData = JSON.stringify({
            code_snippet: codeSnippet,
            file_path: filePath,
            line_numbers: lineNumbers
        });

        const options = {
            hostname: '127.0.0.1',
            port: 8000,
            path: '/context/retrieve',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                if (res.statusCode === 200) {
                    try {
                        const contextObjects = JSON.parse(data);
                        this.renderContextCards(contextObjects);
                    } catch (e) {
                        this.showError("Failed to parse context response.");
                    }
                } else {
                    this.showError(`Error: Server returned ${res.statusCode}`);
                }
            });
        });

        req.on('error', (e) => {
            this.showError("Context Engine Disconnected. Is the Python server running?");
        });

        req.write(postData);
        req.end();
    }

    public triggerSync() {
        const options = {
            hostname: '127.0.0.1',
            port: 8000,
            path: '/context/sync',
            method: 'POST'
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                if (res.statusCode === 200) {
                    try {
                        const result = JSON.parse(data);
                        vscode.window.showInformationMessage(`Synced ${result.items_synced} items from Slack/Jira`);
                    } catch (e) {
                        vscode.window.showWarningMessage("Sync completed but response was invalid.");
                    }
                } else {
                    vscode.window.showErrorMessage(`Sync failed: ${res.statusCode}`);
                }
            });
        });

        req.on('error', (e) => {
            vscode.window.showErrorMessage("Sync failed: Server unreachable");
        });

        req.end();
    }

    private renderContextCards(contextObjects: any[]) {
        if (this._view) {
            const cardsHtml = contextObjects.map((obj, idx) => {
                const sourceClass = obj.source.toLowerCase();
                const icon = sourceClass === 'slack' ? '#' : '🎫';
                return `
                <div class="context-card ${sourceClass}">
                    <div class="context-header">
                        <span class="context-badge">${icon} ${obj.source.toUpperCase()}</span>
                        <span class="context-user">${obj.title_or_user}</span>
                    </div>
                    <div class="context-summary">${this.escapeHtml(obj.content_summary)}</div>
                    ${obj.url ? `<a href="${obj.url}" class="context-link">Open in ${obj.source}</a>` : ''}
                </div>
            `;
            }).join('');

            const containerHtml = `
                <h3>Raw Context Data</h3>
                <div class="cards-container">
                    ${cardsHtml}
                </div>
                <button onclick="syncNow()" class="sync-button">🔄 Sync Now</button>
            `;

            this._view.webview.html = this._getHtmlForWebview(containerHtml, false, true);
        }
    }

    private escapeHtml(text: string): string {
        return text.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;')
            .replace(/\n/g, '<br>');
    }

    private updateContent(markdown: string) {
        if (this._view) {
            const html = `
                <div class="explanation-container">
                    <div id="markdown-content"></div>
                    <div class="actions">
                        <button onclick="copyText()" class="action-button">📋 Copy</button>
                    </div>
                </div>
            `;
            this._view.webview.html = this._getHtmlForWebview(html, true, false, markdown);
        }
    }

    private showError(message: string) {
        if (this._view) {
            this._view.webview.html = this._getHtmlForWebview(`
                <div class="error-container">
                    <h3>⚠️ Error</h3>
                    <p>${message}</p>
                </div>
            `);
        }
    }

    private _getHtmlForWebview(content: string, isMarkdown: boolean = false, isContextCards: boolean = false, rawMarkdown: string = "") {
        const script = `
        <script src="https://cdn.jsdelivr.net/npm/markdown-it@13.0.1/dist/markdown-it.min.js"></script>
        <script>
            const vscode = acquireVsCodeApi();
            
            // Markdown Rendering
            if (${isMarkdown}) {
                const md = window.markdownit();
                const rawContent = \`${rawMarkdown.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`;
                document.getElementById('markdown-content').innerHTML = md.render(rawContent);
            }

            // Sync Action
            function syncNow() {
                vscode.postMessage({ command: 'sync' });
            }

            // Copy Action
            function copyText() {
                const text = document.body.innerText;
                vscode.postMessage({ command: 'copy', text: text });
            }
        </script>
        `;

        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {
                    --container-padding: 20px;
                    --input-padding-vertical: 6px;
                    --input-padding-horizontal: 4px;
                    --input-margin-vertical: 4px;
                    --input-margin-horizontal: 0;
                }

                body {
                    padding: 0;
                    color: var(--vscode-editor-foreground);
                    font-family: var(--vscode-font-family);
                    font-weight: var(--vscode-font-weight);
                    font-size: var(--vscode-font-size);
                }

                /* Welcome State */
                .welcome-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    text-align: center;
                    padding: 20px;
                    color: var(--vscode-descriptionForeground);
                }
                .welcome-container .icon { font-size: 3em; margin-bottom: 10px; opacity: 0.5; }

                /* Loading State */
                .loader-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                }
                .spinner {
                    border: 4px solid var(--vscode-widget-shadow);
                    border-top: 4px solid var(--vscode-progressBar-background);
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    animation: spin 1s linear infinite;
                    margin-bottom: 10px;
                }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

                /* Cards */
                .cards-container { padding: 10px; }
                .context-card {
                    background-color: var(--vscode-sideBar-background);
                    border: 1px solid var(--vscode-widget-border);
                    border-left-width: 4px;
                    padding: 12px;
                    margin-bottom: 10px;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.1s;
                }
                .context-card:hover { transform: translateY(-2px); }
                
                .context-card.slack { border-left-color: #E01E5A; }
                .context-card.jira { border-left-color: #0052CC; }

                .context-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    font-size: 0.85em;
                }
                .context-badge {
                    font-weight: bold;
                    opacity: 0.8;
                }
                .context-user { opacity: 0.6; }
                .context-summary { margin-bottom: 8px; line-height: 1.4; }
                .context-link { color: var(--vscode-textLink-foreground); text-decoration: none; font-size: 0.9em; }
                .context-link:hover { text-decoration: underline; }

                /* Markdown Content */
                .explanation-container { padding: 15px; }
                #markdown-content h1, #markdown-content h2, #markdown-content h3 { border-bottom: 1px solid var(--vscode-widget-border); padding-bottom: 5px; }
                blockquote {
                    background: var(--vscode-textBlockQuote-background);
                    border-left: 4px solid var(--vscode-textBlockQuote-border);
                    margin: 0;
                    padding: 4px 10px;
                }
                code {
                    font-family: var(--vscode-editor-font-family);
                    background: var(--vscode-textCodeBlock-background);
                    padding: 2px 4px;
                    border-radius: 3px;
                }

                /* Buttons */
                button {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 6px 12px;
                    border-radius: 2px;
                    cursor: pointer;
                }
                button:hover { background: var(--vscode-button-hoverBackground); }
                .sync-button { width: 100%; margin-top: 10px; }
                .action-button { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); }
                .action-button:hover { background: var(--vscode-button-secondaryHoverBackground); }
                .actions { margin-top: 15px; border-top: 1px solid var(--vscode-widget-border); padding-top: 10px; }

                /* Error */
                .error-container { padding: 20px; color: var(--vscode-errorForeground); text-align: center; }
            </style>
        </head>
        <body>
            ${content}
            ${script}
        </body>
        </html>`;
    }
}
