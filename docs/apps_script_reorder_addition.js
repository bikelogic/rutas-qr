
const REORDER_START_ROW = 2;
const REORDER_ZONE_COLS = {
  fabriques: { addr: 7, code: 8 },
  centre: { addr: 10, code: 11 },
  mirasol: { addr: 13, code: 14 },
  altres: { addr: 16, code: 17 },
};

function doGet() {
  return jsonResponse({ ok: true, message: 'BikeLogic reorder API online' });
}

function doPost(e) {
  try {
    const body = JSON.parse((e && e.postData && e.postData.contents) || '{}');

    if (body.action !== 'reorder') {
      return jsonResponse({ ok: false, message: 'Accio no valida' });
    }

    return handleReorder(body);
  } catch (error) {
    return jsonResponse({ ok: false, message: error.message });
  }
}

function handleReorder(data) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getActiveSheet();
  const zones = data.zones || {};
  const existingRows = Math.max(0, sheet.getLastRow() - REORDER_START_ROW + 1);

  Object.keys(REORDER_ZONE_COLS).forEach(function(zoneId) {
    const cols = REORDER_ZONE_COLS[zoneId];
    const items = Array.isArray(zones[zoneId]) ? zones[zoneId] : [];
    const newCount = items.length;
    const clearCount = Math.max(0, existingRows - newCount);

    if (newCount > 0) {
      const addrValues = items.map(function(item) { return [sanitizeCell(item.addr)]; });
      const codeValues = items.map(function(item) { return [sanitizeCell(item.code)]; });

      sheet.getRange(REORDER_START_ROW, cols.addr, newCount, 1).setValues(addrValues);
      sheet.getRange(REORDER_START_ROW, cols.code, newCount, 1).setValues(codeValues);
    }

    if (clearCount > 0) {
      const clearStart = REORDER_START_ROW + newCount;
      sheet.getRange(clearStart, cols.addr, clearCount, 1).clearContent();
      sheet.getRange(clearStart, cols.code, clearCount, 1).clearContent();
    }
  });

  SpreadsheetApp.flush();

  return jsonResponse({
    ok: true,
    message: 'Ordre actualitzat correctament',
    updatedAt: new Date().toISOString(),
  });
}

function sanitizeCell(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value).trim();
}

function jsonResponse(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
