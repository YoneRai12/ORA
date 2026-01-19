const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1280,
        height: 800,
        title: "ORA AI OS",
        backgroundColor: '#0d0d17',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
        icon: path.join(__dirname, 'public/icons/icon-512x512.png')
    });

    // In development, load from localhost
    // In production, we would use electron-serve or similar
    const url = process.env.NODE_ENV === 'development'
        ? 'http://localhost:3333'
        : `file://${path.join(__dirname, 'out/index.html')}`;

    win.loadURL(url);

    // Remove menu for premium feel
    win.setMenuBarVisibility(false);
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});
