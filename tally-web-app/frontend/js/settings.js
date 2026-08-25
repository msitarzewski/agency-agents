/**
 * SETTINGS.JS — connection / sync / preferences + Tally test button
 */
(function () {
  'use strict';
  const { $, toast } = App;

  const FIELDS = ['tallyHost', 'tallyPort', 'companyName', 'demoMode', 'syncIntervalSec',
    'odbcEnabled', 'odbcDsn', 'theme', 'defaultPrint', 'invoicePrefix', 'defaultVoucherView', 'autoRoundOff'];

  async function load() {
    try {
      const s = await App.api('/settings');
      FIELDS.forEach((f) => {
        const el = $(`#set-${f}`);
        if (!el) return;
        if (el.type === 'checkbox') el.checked = !!s[f];
        else el.value = s[f] ?? '';
      });
    } catch (e) { toast('error', 'Could not load settings', e.message); }
  }

  async function save() {
    const body = {};
    FIELDS.forEach((f) => {
      const el = $(`#set-${f}`);
      if (!el) return;
      let v = el.value;
      if (f === 'tallyPort' || f === 'syncIntervalSec') v = Number(v);
      if (f === 'odbcEnabled' || f === 'autoRoundOff') v = el.value === 'true';
      body[f] = v;
    });
    const btn = $('#settingsSave');
    App.loading(btn, true, 'Saving…');
    try {
      const res = await App.apiRaw('/settings', { method: 'PUT', body });
      if (res.success) {
        toast('success', 'Settings saved', 'Applied instantly — no restart needed');
        if (body.theme) App.theme.set(body.theme);
      } else toast('error', 'Could not save', res.error?.message);
    } catch { /* handled */ }
    finally { App.loading(btn, false); }
  }

  async function testConnection() {
    const btn = $('#testConnBtn');
    const box = $('#connResult');
    App.loading(btn, true, 'Testing…');
    box.innerHTML = `<div class="empty-state" style="padding:16px"><i class="fa-solid fa-spinner fa-spin"></i>Pinging Tally…</div>`;
    try {
      const res = await App.apiRaw('/company/test');
      if (res.success) {
        box.innerHTML = `<div class="badge badge-success" style="font-size:13px;padding:10px 14px">
          <i class="fa-solid fa-circle-check"></i> ${res.message} — companies: ${res.data.companies.join(', ') || '(active company)'}</div>`;
      } else {
        box.innerHTML = `<div class="badge badge-danger" style="font-size:13px;padding:10px 14px;white-space:normal">
          <i class="fa-solid fa-circle-xmark"></i> ${res.error.message}</div>
          <p style="font-size:12px;color:var(--muted)">${res.error.hint || ''}</p>`;
      }
    } catch (e) {
      box.innerHTML = `<div class="badge badge-danger" style="font-size:13px;padding:10px 14px">Request failed: ${e.message}</div>`;
    } finally { App.loading(btn, false); }
  }

  document.addEventListener('DOMContentLoaded', () => {
    load();
    $('#settingsSave').addEventListener('click', save);
    $('#settingsReset').addEventListener('click', async () => {
      const ok = await App.confirm('Reset all settings?', 'Everything returns to defaults.', 'warning');
      if (!ok.isConfirmed) return;
      await App.api('/settings/reset', { method: 'POST' });
      load();
      toast('info', 'Settings reset');
    });
    $('#testConnBtn').addEventListener('click', testConnection);
  });
})();
