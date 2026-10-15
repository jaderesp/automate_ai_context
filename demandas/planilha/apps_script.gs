// Integracao do agente com a planilha "Uzapi - Bugs e Melhorias".
// Regras: ai.context/demandas/regras/FONTE_BACKLOG.md
// Publicado como app da Web; toda chamada exige o token de Propriedades do script (SYNC_TOKEN).
// Acoes (POST JSON): {"token","action":"export"} | {"token","action":"history","since"} | {"token","action":"get","id"} | {"token","action":"update","id","status","versao","observacao"}
// Status so aceita "Concluido"; versao substitui; observacao e acrescentada. Nenhuma outra coluna e alterada.

var SPREADSHEET_ID = '1jhUffmbFYd4yaiRzsbA5pQoLBiqdlsf-170L7e0Gby4';
var HEADER_ID = 'ID';
var HEADER_STATUS = 'Status';
var HEADER_VERSAO = 'Vers\u00e3o';
var HEADER_OBS = 'Observa\u00e7\u00f5es';
var STATUS_PERMITIDOS = ['Conclu\u00eddo'];

function doPost(e) {
  try {
    var body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var token = PropertiesService.getScriptProperties().getProperty('SYNC_TOKEN');
    if (!token || body.token !== token) {
      return json_({ ok: false, error: 'token inv\u00e1lido' });
    }
    if (body.action === 'history') return json_({ ok: true, history: historico_(body.since) });
    if (body.action === 'export') return json_(exportar_());

    var id = String(body.id || '').replace(/^DEM-/i, '').trim();
    if (!id) return json_({ ok: false, error: 'id obrigat\u00f3rio' });

    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      var alvo = localizar_(id);
      if (!alvo) return json_({ ok: false, error: 'task ' + id + ' n\u00e3o encontrada' });

      if (body.action === 'get') return json_({ ok: true, task: ler_(alvo) });
      if (body.action !== 'update') return json_({ ok: false, error: 'a\u00e7\u00e3o inv\u00e1lida' });

      var antes = ler_(alvo);
      var c = alvo.cols;
      var sheet = alvo.sheet;
      var row = alvo.row;

      if (body.status !== undefined) {
        if (STATUS_PERMITIDOS.indexOf(body.status) < 0) {
          return json_({ ok: false, error: 'status n\u00e3o permitido: ' + body.status });
        }
      }
      if (body.status !== undefined) sheet.getRange(row, c.status).setValue(body.status);
      if (body.versao !== undefined) {
        // '@' = texto puro: impede o Sheets de converter "0.095" em numero.
        sheet.getRange(row, c.versao).setNumberFormat('@').setValue(String(body.versao));
      }
      if (body.observacao) {
        var atual = String(sheet.getRange(row, c.obs).getValue() || '').trim();
        var novo = atual ? atual + '\n\n' + body.observacao : body.observacao;
        sheet.getRange(row, c.obs).setValue(novo);
      }
      SpreadsheetApp.flush();
      return json_({ ok: true, antes: antes, depois: ler_(alvo) });
    } finally {
      lock.releaseLock();
    }
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function localizar_(id) {
  var sheets = SpreadsheetApp.openById(SPREADSHEET_ID).getSheets();
  for (var s = 0; s < sheets.length; s++) {
    var sheet = sheets[s];
    var lastCol = sheet.getLastColumn();
    if (lastCol < 1) continue;
    var header = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(String);
    var cols = {
      id: header.indexOf(HEADER_ID) + 1,
      status: header.indexOf(HEADER_STATUS) + 1,
      versao: header.indexOf(HEADER_VERSAO) + 1,
      obs: header.indexOf(HEADER_OBS) + 1,
    };
    if (!cols.id || !cols.status || !cols.versao || !cols.obs) continue;
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) continue;
    var ids = sheet.getRange(2, cols.id, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) {
      if (String(ids[i][0]).replace(/^DEM-/i, '').trim() === id) {
        return { sheet: sheet, row: i + 2, cols: cols };
      }
    }
  }
  return null;
}

function ler_(alvo) {
  var g = function (col) { return alvo.sheet.getRange(alvo.row, col).getDisplayValue(); };
  return {
    aba: alvo.sheet.getName(),
    linha: alvo.row,
    status: g(alvo.cols.status),
    versao: g(alvo.cols.versao),
    observacoes: g(alvo.cols.obs),
  };
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}


// ---------------------------------------------------------------------------
// Monitoramento de alteracoes feitas por pessoas (gatilho instalavel "ao editar").
// Gravacoes feitas por este script (doPost) NAO disparam o gatilho.
// Instalar: rodar instalarGatilho() uma vez no editor do Apps Script.

var NOTIFY_EMAIL = 'jaderesp@gmail.com';
var HIST_SHEET = 'Hist\u00f3rico';
var HIST_HEADER = ['Data', 'Usu\u00e1rio', 'Aba', 'Linha', 'Task', 'Coluna', 'Antes', 'Depois'];
var HEADER_TESTADO = 'Testado Em';

function instalarGatilho() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'aoEditar') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('aoEditar').forSpreadsheet(SPREADSHEET_ID).onEdit().create();
  abaHistorico_();
  MailApp.sendEmail(NOTIFY_EMAIL, '[UzAPI planilha] Monitoramento ativado',
    'A partir de agora, altera\u00e7\u00f5es feitas por pessoas na planilha ficam na aba "' + HIST_SHEET +
    '" e as importantes chegam neste e-mail.');
}

function aoEditar(e) {
  try {
    var sheet = e.range.getSheet();
    if (sheet.getName() === HIST_SHEET) return;
    var lastCol = sheet.getLastColumn();
    var header = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(String);
    var colId = header.indexOf(HEADER_ID) + 1;
    if (!colId || header.indexOf(HEADER_STATUS) < 0) return;

    var user = (e.user && e.user.getEmail && e.user.getEmail()) || '';
    var agora = new Date();
    var unica = e.range.getNumRows() === 1 && e.range.getNumColumns() === 1;
    var linhas = [];
    var importantes = [];

    for (var r = 0; r < e.range.getNumRows(); r++) {
      var row = e.range.getRow() + r;
      if (row < 2) continue;
      var task = String(sheet.getRange(row, colId).getDisplayValue() || '');
      for (var c = 0; c < e.range.getNumColumns(); c++) {
        var col = e.range.getColumn() + c;
        var coluna = header[col - 1] || ('Coluna ' + col);
        var depois = unica ? (e.value === undefined ? '' : String(e.value))
                           : String(sheet.getRange(row, col).getDisplayValue() || '');
        var antes = unica ? (e.oldValue === undefined ? '' : String(e.oldValue)) : '(edi\u00e7\u00e3o em bloco)';
        if (antes === depois) continue;
        linhas.push([agora, user, sheet.getName(), row, task, coluna, antes, depois]);

        // Linhas ja vem numeradas: task nova = ID novo ou Titulo preenchido numa linha vazia.
        var novaTask = (coluna === HEADER_ID || coluna === 'T\u00edtulo') && !antes && depois;
        if (novaTask || coluna === HEADER_STATUS || coluna === HEADER_OBS || coluna === HEADER_TESTADO) {
          importantes.push((novaTask ? 'Task nova: DEM-' + task + ' ' + resumo_(depois)
            : 'DEM-' + task + ' \u2014 ' + coluna + ': "' + resumo_(antes) + '" \u2192 "' + resumo_(depois) + '"'));
        }
      }
    }
    if (!linhas.length) return;
    var hist = abaHistorico_();
    hist.getRange(hist.getLastRow() + 1, 1, linhas.length, HIST_HEADER.length).setValues(linhas);

    if (importantes.length) {
      var assunto = '[UzAPI planilha] ' + importantes[0] + (importantes.length > 1 ? ' (+' + (importantes.length - 1) + ')' : '');
      MailApp.sendEmail(NOTIFY_EMAIL, assunto.slice(0, 240),
        importantes.join('\n') + '\n\nPor: ' + (user || 'n\u00e3o informado') +
        '\nPlanilha: https://docs.google.com/spreadsheets/d/' + SPREADSHEET_ID + '/edit');
    }
  } catch (err) {
    console.error('aoEditar: ' + err);
  }
}

function abaHistorico_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var hist = ss.getSheetByName(HIST_SHEET);
  if (!hist) {
    hist = ss.insertSheet(HIST_SHEET);
    hist.getRange(1, 1, 1, HIST_HEADER.length).setValues([HIST_HEADER]).setFontWeight('bold');
    hist.setFrozenRows(1);
  }
  return hist;
}

function historico_(since) {
  var hist = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(HIST_SHEET);
  if (!hist || hist.getLastRow() < 2) return [];
  var desde = since ? new Date(since) : new Date(0);
  return hist.getRange(2, 1, hist.getLastRow() - 1, HIST_HEADER.length).getValues()
    .filter(function (r) { return r[0] instanceof Date && r[0] > desde; })
    .map(function (r) {
      return { data: r[0].toISOString(), usuario: r[1], aba: r[2], linha: r[3], task: String(r[4]),
               coluna: r[5], antes: String(r[6]), depois: String(r[7]) };
    });
}

function resumo_(v) {
  v = String(v || '').replace(/\s+/g, ' ');
  return v.length > 80 ? v.slice(0, 77) + '...' : v;
}

// Exporta a aba principal (a que tem ID, Status, Versao e Observacoes) como
// cabecalho + linhas com valores exibidos; linhas sem ID e sem titulo ficam de fora.
function exportar_() {
  var sheets = SpreadsheetApp.openById(SPREADSHEET_ID).getSheets();
  for (var s = 0; s < sheets.length; s++) {
    var sheet = sheets[s];
    if (sheet.getName() === HIST_SHEET) continue;
    var lastCol = sheet.getLastColumn();
    var lastRow = sheet.getLastRow();
    if (lastCol < 1 || lastRow < 1) continue;
    var values = sheet.getRange(1, 1, lastRow, lastCol).getDisplayValues();
    var header = values[0].map(String);
    if (header.indexOf(HEADER_ID) < 0 || header.indexOf(HEADER_STATUS) < 0) continue;
    var colTitulo = header.indexOf('T\u00edtulo');
    var colId = header.indexOf(HEADER_ID);
    var rows = values.slice(1).filter(function (r) {
      return String(r[colId]).trim() || (colTitulo >= 0 && String(r[colTitulo]).trim());
    });
    return { ok: true, aba: sheet.getName(), header: header, rows: rows };
  }
  return { ok: false, error: 'aba principal n\u00e3o encontrada' };
}
