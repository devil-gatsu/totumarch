const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const xlsx = require('xlsx');
const ExcelJS = require('exceljs');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 600,
    height: 680,
    resizable: false,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Abre a janela de seleção de arquivos
ipcMain.handle('selecionar-arquivos', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [{ name: 'Planilhas', extensions: ['csv', 'txt', 'xlsx', 'xls'] }]
  });
  return result.filePaths;
});

// Lê o arquivo e converte para JSON
function lerArquivo(caminho, tipo) {
  const workbook = xlsx.readFile(caminho);
  const sheetName = workbook.SheetNames[0];
  const data = xlsx.utils.sheet_to_json(workbook.Sheets[sheetName], { raw: false, defval: "" });
  return data.map(row => {
    let newRow = {};
    for (let key in row) {
      newRow[key.trim().toUpperCase()] = String(row[key]).trim();
    }
    newRow['TIPO'] = tipo;
    return newRow;
  });
}

// Processamento da Auditoria
ipcMain.handle('processar-auditoria', async (event, dados) => {
  try {
    let listAtuais = [];
    let listConf = [];

    // Compila os dados baseados no modo
    if (dados.modo === 'AP') {
      dados.arquivos.apAtual.forEach(f => listAtuais.push(...lerArquivo(f, 'AP')));
      dados.arquivos.apConf.forEach(f => listConf.push(...lerArquivo(f, 'AP')));
    } else if (dados.modo === 'EDUC') {
      dados.arquivos.educAtual.forEach(f => listAtuais.push(...lerArquivo(f, 'EDUC')));
      dados.arquivos.educConf.forEach(f => listConf.push(...lerArquivo(f, 'EDUC')));
    } else {
      dados.arquivos.apAtual.forEach(f => listAtuais.push(...lerArquivo(f, 'AP')));
      dados.arquivos.educAtual.forEach(f => listAtuais.push(...lerArquivo(f, 'EDUC')));
      dados.arquivos.apConf.forEach(f => listConf.push(...lerArquivo(f, 'AP')));
      dados.arquivos.educConf.forEach(f => listConf.push(...lerArquivo(f, 'EDUC')));
    }

    if (listAtuais.length === 0 || listConf.length === 0) throw new Error("Faltam arquivos para comparar.");

    // Dicionário de cruzamento
    let oldData = { 'AP': {}, 'EDUC': {} };
    listConf.forEach(row => {
      let tipo = row['TIPO'];
      let nome = row['NOME DO SEGURADO'] ? row['NOME DO SEGURADO'].toUpperCase() : '';
      if (!nome) return;

      if (!oldData[tipo][nome]) oldData[tipo][nome] = { MAT: [], CERT: [], CPF: [], NASC: [] };
      
      if (row['MATRICULA']) oldData[tipo][nome].MAT.push(row['MATRICULA'].toUpperCase());
      if (row['CERTIFICADO']) oldData[tipo][nome].CERT.push(row['CERTIFICADO'].toUpperCase());
      if (row['CPF']) oldData[tipo][nome].CPF.push(row['CPF'].toUpperCase());
      if (row['DATA DE NASCIMENTO']) oldData[tipo][nome].NASC.push(row['DATA DE NASCIMENTO'].toUpperCase());
    });

    let contAp = 0;
    let contEduc = 0;
    let errosTotais = [];

    listAtuais.forEach(row => {
      let tipo = row['TIPO'];
      let nome = row['NOME DO SEGURADO'] ? row['NOME DO SEGURADO'].toUpperCase() : '';
      if (!nome) return;

      let cpfAtual = row['CPF'] ? row['CPF'].toUpperCase() : '';
      let matAtual = row['MATRICULA'] ? row['MATRICULA'].toUpperCase() : '';
      let certAtual = row['CERTIFICADO'] ? row['CERTIFICADO'].toUpperCase() : '';
      let nascAtual = row['DATA DE NASCIMENTO'] ? row['DATA DE NASCIMENTO'].toUpperCase() : '';

      let inconsistencias = [];

      if (!oldData[tipo][nome]) {
        inconsistencias.push("NOME INEXISTENTE NA BASE ANTERIOR");
      } else {
        if (!oldData[tipo][nome].MAT.includes(matAtual)) inconsistencias.push("DIVERGÊNCIA DE MATRÍCULA");
        if (!oldData[tipo][nome].CERT.includes(certAtual)) inconsistencias.push("DIVERGÊNCIA DE CERTIFICADO");
        if (!oldData[tipo][nome].NASC.includes(nascAtual)) inconsistencias.push("DIVERGÊNCIA DE NASCIMENTO");
        
        // Apenas EDUC valida CPF
        if (tipo === 'EDUC' && !oldData[tipo][nome].CPF.includes(cpfAtual)) {
          inconsistencias.push("DIVERGÊNCIA DE CPF");
        }
      }

      if (inconsistencias.length > 0) {
        let cpfRelatorio = tipo === 'EDUC' ? cpfAtual : "N/A (Regra AP)";
        let nomeFormatado = row['NOME DO SEGURADO'];
        
        let linhaErro = { "SEGURADO": nomeFormatado, "CPF": cpfRelatorio };
        inconsistencias.forEach((erro, idx) => {
          linhaErro[`INCONSISTÊNCIA ${idx + 1}`] = `[${tipo}] ${erro}`;
        });
        
        errosTotais.push(linhaErro);
        if (tipo === 'AP') contAp++; else contEduc++;
      }
    });

    if (errosTotais.length === 0) return { ap: 0, educ: 0, success: true, msg: "Nenhuma divergência encontrada!" };

    // Exportação Excel Estilizada
    const savePath = await dialog.showSaveDialog(mainWindow, {
      title: 'Salvar Relatório de Auditoria',
      defaultPath: 'Auditoria_Premium.xlsx',
      filters: [{ name: 'Excel', extensions: ['xlsx'] }]
    });

    if (savePath.canceled) return { ap: contAp, educ: contEduc, success: false, msg: "Exportação cancelada." };

    const wb = new ExcelJS.Workbook();
    const ws = wb.addWorksheet('Auditoria');

    // Cabeçalhos dinâmicos
    let colunasSet = new Set();
    errosTotais.forEach(e => Object.keys(e).forEach(k => colunasSet.add(k)));
    let columns = Array.from(colunasSet).map(c => ({ header: c, key: c, width: 25 }));
    ws.columns = columns;

    ws.addRows(errosTotais);

    // Estilo do cabeçalho
    ws.getRow(1).eachCell((cell) => {
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1F4E78' } };
      cell.font = { color: { argb: 'FFFFFFFF' }, bold: true };
      cell.alignment = { vertical: 'middle', horizontal: 'center' };
    });

    await wb.xlsx.writeFile(savePath.filePath);

    return { ap: contAp, educ: contEduc, success: true, msg: "Relatório gerado com sucesso!" };

  } catch (error) {
    return { success: false, msg: error.message };
  }
});
