import * as vscode from 'vscode';
import { ContextSidebarProvider } from './sidebar';

export function activate(context: vscode.ExtensionContext) {
    console.log('ContextSync extension is activating...');

    try {
        const sidebarProvider = new ContextSidebarProvider(context.extensionUri);

        context.subscriptions.push(
            vscode.window.registerWebviewViewProvider("contextSyncView", sidebarProvider)
        );

        context.subscriptions.push(
            vscode.commands.registerCommand('contextsync.explain', () => {
                const editor = vscode.window.activeTextEditor;
                if (editor) {
                    const selection = editor.selection;
                    const text = editor.document.getText(selection);
                    const filePath = editor.document.fileName;
                    const lineNumbers = `${selection.start.line + 1}-${selection.end.line + 1}`;

                    if (text.trim().length === 0) {
                        vscode.window.showWarningMessage('Please highlight some code to explain.');
                        return;
                    }

                    sidebarProvider.showLoading();
                    sidebarProvider.explainCode(text, filePath, lineNumbers);

                    // Focus the sidebar
                    vscode.commands.executeCommand('contextSyncView.focus');
                } else {
                    vscode.window.showWarningMessage('ContextSync: No active text editor.');
                }
            })
        );

        context.subscriptions.push(
            vscode.commands.registerCommand('contextsync.showContext', () => {
                const editor = vscode.window.activeTextEditor;
                if (editor) {
                    const selection = editor.selection;
                    const text = editor.document.getText(selection);
                    const filePath = editor.document.fileName;
                    const lineNumbers = `${selection.start.line + 1}-${selection.end.line + 1}`;

                    if (text.trim().length === 0) {
                        vscode.window.showWarningMessage('Please highlight some code to view context.');
                        return;
                    }

                    sidebarProvider.showLoading();
                    sidebarProvider.fetchContextObjects(text, filePath, lineNumbers);

                    // Focus the sidebar
                    vscode.commands.executeCommand('contextSyncView.focus');
                } else {
                    vscode.window.showWarningMessage('ContextSync: No active text editor.');
                }
            })
        );

        console.log('ContextSync extension activated successfully!');
    } catch (error) {
        console.error('ContextSync activation error:', error);
        vscode.window.showErrorMessage(`ContextSync failed to activate: ${error}`);
    }
}

export function deactivate() { }
