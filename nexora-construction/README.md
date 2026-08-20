# Nexora Construction Management System

A static, responsive construction finance and project workspace for Nexora Limited. It runs immediately in demo mode with localStorage and can be connected to the Apps Script API by setting `CONFIG.API_URL` in `js/config.js`.

## Setup
1. Create a Google Spreadsheet named `Nexora_Construction_DB`.
2. Open **Extensions → Apps Script**, paste `apps-script/Code.gs`, run `setupDatabase` once, and authorize it.
3. Deploy → New deployment → Web app. Execute as you, access for anyone with the link.
4. Copy the `/exec` URL into `CONFIG.API_URL` in `js/config.js`.
5. Host this folder on GitHub Pages or any static host. For a local preview run `python3 -m http.server 8080` from this folder.

Demo login: `prashant` / `Nexora@2025`. Demo records are stored in the browser until an API URL is configured.

> Passwords are SHA-256 hashed by the API. The browser demo uses a non-sensitive demo credential and localStorage; do not use it for production without HTTPS, stronger session management, and restricted sheet sharing.
