/**
 * ============================================================================
 * ERROR HANDLER MIDDLEWARE
 * ============================================================================
 * Central place that converts every thrown error into a clean JSON response:
 *   { success:false, error:{ code, message, hint? } }
 * Tally-specific errors (LINEERROR rejections, unreachable host, queueable
 * writes) arrive here tagged by the services so we can set the right status.
 * ============================================================================
 */

/* 404 for unknown API paths (mounted after all /api routes). */
function apiNotFound(req, res) {
  res.status(404).json({
    success: false,
    error: { code: 'NOT_FOUND', message: `API route ${req.method} ${req.originalUrl} does not exist` },
  });
}

/* eslint-disable no-unused-vars */
function errorHandler(err, req, res, next) {
  const status = err.statusCode || 500;
  const body = {
    success: false,
    error: {
      code: err.code || (status === 422 ? 'VALIDATION_ERROR' : status === 502 ? 'TALLY_ERROR' : 'INTERNAL_ERROR'),
      message: err.message || 'Unexpected server error',
    },
  };
  // Actionable hints for the classic Tally failure modes.
  if (err.tallyUnreachable) {
    body.error.code = 'TALLY_UNREACHABLE';
    body.error.hint = 'Start Tally Prime with the company open, or check host/port in Settings. Your entry will be queued and pushed automatically on reconnect.';
  } else if (err.name === 'OdbcUnavailableError') {
    body.error.code = 'ODBC_UNAVAILABLE';
    body.error.hint = "Run `npm run setup:odbc` on the Windows machine that hosts the Tally DSN, or disable ODBC in Settings (reads will use the XML API).";
  } else if (status === 502) {
    body.error.hint = 'Tally rejected the request — the message usually names the missing ledger/master. Fix it in Tally or create it from the Ledger Master page.';
  }
  if (process.env.NODE_ENV !== 'production' && status >= 500 && !err.tallyUnreachable) {
    console.error('[error]', err);
  }
  res.status(status).json(body);
}

module.exports = { errorHandler, apiNotFound };
