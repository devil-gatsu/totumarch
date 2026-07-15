import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import time
import re
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AuditorSeguradosPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Auditoria de Segurados Pro")
        self.geometry("550x600")
        self.resizable(False, False)
        
        # Variáveis de Arquivos
        self.arquivos = {
            "AP": {"atual": [], "conf": []},
            "EDUC": {"atual": [], "conf": []},
            "AMBOS": {"ap_atual": [], "ap_conf": [], "educ_atual": [], "educ_conf": []}
        }
        
        # Abas independentes
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color="#18181a", segmented_button_selected_color="#2c5e9e")
        self.tabview.pack(padx=20, pady=15, fill="both", expand=True)
        
        self.tab_ap = self.tabview.add("📊 Somente AP")
        self.tab_educ = self.tabview.add("🎓 Somente EDUC")
        self.tab_ambos = self.tabview.add("🔗 AMBOS (Misto)")
        
        self.construir_aba_ap()
        self.construir_aba_educ()
        self.construir_aba_ambos()

        # Rodapé comum
        self.frame_rodape = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_rodape.pack(fill="x", padx=20, pady=(0, 15))

        self.entry_erros = ctk.CTkEntry(self.frame_rodape, placeholder_text="Erros no Sistema (Opcional)", justify="center", width=250, border_color="#333")
        self.entry_erros.pack(pady=5)

        self.progress = ctk.CTkProgressBar(self.frame_rodape, width=400, height=6, progress_color="#2c5e9e")
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.lbl_status = ctk.CTkLabel(self.frame_rodape, text="", font=("Segoe UI", 13, "bold"), justify="center")
        self.lbl_status.pack()

    # ==================================================
    # CONSTRUÇÃO DAS ABAS
    # ==================================================
    def construir_aba_ap(self):
        self.criar_bloco_upload(self.tab_ap, "AP", "atual", "1. Arquivo(s) AP ATUAL")
        self.criar_bloco_upload(self.tab_ap, "AP", "conf", "2. Arquivo(s) AP ANTERIOR")
        btn_exec = ctk.CTkButton(self.tab_ap, text="⚡ Processar Auditoria AP", height=45, fg_color="#27ae60", hover_color="#219653", command=lambda: self.iniciar("AP"))
        btn_exec.pack(pady=20, fill="x", padx=40)

    def construir_aba_educ(self):
        self.criar_bloco_upload(self.tab_educ, "EDUC", "atual", "1. Arquivo(s) EDUC ATUAL")
        self.criar_bloco_upload(self.tab_educ, "EDUC", "conf", "2. Arquivo(s) EDUC ANTERIOR")
        btn_exec = ctk.CTkButton(self.tab_educ, text="⚡ Processar Auditoria EDUC", height=45, fg_color="#8e44ad", hover_color="#732d91", command=lambda: self.iniciar("EDUC"))
        btn_exec.pack(pady=20, fill="x", padx=40)

    def construir_aba_ambos(self):
        frame_grid = ctk.CTkFrame(self.tab_ambos, fg_color="transparent")
        frame_grid.pack(fill="both", expand=True, pady=10)
        
        # Coluna AP
        frame_esq = ctk.CTkFrame(frame_grid, fg_color="#1f2329", corner_radius=8)
        frame_esq.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(frame_esq, text="Dados AP", font=("Segoe UI", 12, "bold"), text_color="#3498db").pack(pady=5)
        self.criar_bloco_upload(frame_esq, "AMBOS", "ap_atual", "AP Atual", largura=160)
        self.criar_bloco_upload(frame_esq, "AMBOS", "ap_conf", "AP Anterior", largura=160)

        # Coluna EDUC
        frame_dir = ctk.CTkFrame(frame_grid, fg_color="#2a222d", corner_radius=8)
        frame_dir.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkLabel(frame_dir, text="Dados EDUC", font=("Segoe UI", 12, "bold"), text_color="#9b59b6").pack(pady=5)
        self.criar_bloco_upload(frame_dir, "AMBOS", "educ_atual", "EDUC Atual", largura=160)
        self.criar_bloco_upload(frame_dir, "AMBOS", "educ_conf", "EDUC Anterior", largura=160)

        btn_exec = ctk.CTkButton(self.tab_ambos, text="⚡ Processar Auditoria COMPLETA", height=45, fg_color="#d35400", hover_color="#a84300", command=lambda: self.iniciar("AMBOS"))
        btn_exec.pack(pady=10, fill="x", padx=40)

    def criar_bloco_upload(self, parent, aba, chave, texto_btn, largura=250):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=10)
        btn = ctk.CTkButton(frame, text="📁 " + texto_btn, width=largura, fg_color="#333", hover_color="#444", border_width=1, border_color="#555",
                            command=lambda: self.selecionar_arquivos(aba, chave, lbl))
        btn.pack()
        lbl = ctk.CTkLabel(frame, text="Nenhum arquivo", text_color="#666", font=("Segoe UI", 10))
        lbl.pack()

    def selecionar_arquivos(self, aba, chave, lbl_ref):
        arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos CSV/TXT/Excel", "*.txt *.csv *.TXT *.xlsx *.xls")])
        if arquivos:
            self.arquivos[aba][chave] = arquivos
            lbl_ref.configure(text=f"{len(arquivos)} arquivo(s)", text_color="#00FF7F")

    # ==================================================
    # LÓGICA DE AUDITORIA E ANIMAÇÃO
    # ==================================================
    def iniciar(self, modo):
        self.progress.set(0)
        self.animar_texto(self.lbl_status, "Preparando cruzamento de dados...", "#F1C40F")
        threading.Thread(target=self.processar, args=(modo,)).start()

    def animar_texto(self, label, texto, cor):
        label.configure(text="", text_color=cor)
        texto_atual = ""
        for char in texto:
            texto_atual += char
            label.configure(text=texto_atual)
            self.update_idletasks()
            time.sleep(0.015)

    def ler_arquivo(self, caminho):
        if caminho.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(caminho, dtype=str).fillna("")
        else:
            try: return pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig').fillna("")
            except: return pd.read_csv(caminho, sep=';', dtype=str, encoding='latin-1').fillna("")

    def processar(self, modo):
        try:
            list_atuais, list_conf = [], []
            
            # Reúne os arquivos conforme a aba selecionada
            if modo == "AP":
                for f in self.arquivos["AP"]["atual"]: df = self.ler_arquivo(f); df['TIPO'] = "AP"; list_atuais.append(df)
                for f in self.arquivos["AP"]["conf"]: df = self.ler_arquivo(f); df['TIPO'] = "AP"; list_conf.append(df)
            elif modo == "EDUC":
                for f in self.arquivos["EDUC"]["atual"]: df = self.ler_arquivo(f); df['TIPO'] = "EDUC"; list_atuais.append(df)
                for f in self.arquivos["EDUC"]["conf"]: df = self.ler_arquivo(f); df['TIPO'] = "EDUC"; list_conf.append(df)
            else:
                for f in self.arquivos["AMBOS"]["ap_atual"]: df = self.ler_arquivo(f); df['TIPO'] = "AP"; list_atuais.append(df)
                for f in self.arquivos["AMBOS"]["educ_atual"]: df = self.ler_arquivo(f); df['TIPO'] = "EDUC"; list_atuais.append(df)
                for f in self.arquivos["AMBOS"]["ap_conf"]: df = self.ler_arquivo(f); df['TIPO'] = "AP"; list_conf.append(df)
                for f in self.arquivos["AMBOS"]["educ_conf"]: df = self.ler_arquivo(f); df['TIPO'] = "EDUC"; list_conf.append(df)

            if not list_atuais or not list_conf:
                self.animar_texto(self.lbl_status, "ERRO: Faltam arquivos para comparar.", "#FF4D4D")
                return

            df_atual = pd.concat(list_atuais, ignore_index=True)
            df_conf = pd.concat(list_conf, ignore_index=True)
            
            self.progress.set(0.3)
            
            # Construção do Dicionário
            old_data = {'AP': {}, 'EDUC': {}}
            for _, row in df_conf.iterrows():
                tipo = row['TIPO']
                nome = str(row.get('NOME DO SEGURADO', '')).strip().upper()
                if not nome: continue
                if nome not in old_data[tipo]: old_data[tipo][nome] = {'MAT': [], 'CERT': [], 'CPF': [], 'NASC': []}
                
                old_data[tipo][nome]['MAT'].append(str(row.get('MATRICULA', '')).strip().upper())
                old_data[tipo][nome]['CERT'].append(str(row.get('CERTIFICADO', '')).strip().upper())
                old_data[tipo][nome]['CPF'].append(str(row.get('CPF', '')).strip().upper())
                old_data[tipo][nome]['NASC'].append(str(row.get('DATA DE NASCIMENTO', '')).strip().upper())

            self.progress.set(0.5)
            
            erros_totais = {}
            cont_ap, cont_educ = 0, 0
            total_linhas = len(df_atual)

            for idx, row in df_atual.iterrows():
                if idx % 30 == 0:
                    self.progress.set(0.5 + (0.4 * (idx / total_linhas)))
                    self.update_idletasks()

                tipo = row['TIPO']
                nome = str(row.get('NOME DO SEGURADO', '')).strip().upper()
                if not nome: continue

                cpf_atual = str(row.get('CPF', '')).strip().upper()
                mat_atual = str(row.get('MATRICULA', '')).strip().upper()
                cert_atual = str(row.get('CERTIFICADO', '')).strip().upper()
                nasc_atual = str(row.get('DATA DE NASCIMENTO', '')).strip().upper()

                inconsistencias = []

                if nome not in old_data[tipo]:
                    inconsistencias.append("NOME INEXISTENTE NA BASE ANTERIOR")
                else:
                    if mat_atual not in old_data[tipo][nome]['MAT']: inconsistencias.append(f"DIVERGÊNCIA DE MATRÍCULA")
                    if cert_atual not in old_data[tipo][nome]['CERT']: inconsistencias.append(f"DIVERGÊNCIA DE CERTIFICADO")
                    if nasc_atual not in old_data[tipo][nome]['NASC']: inconsistencias.append(f"DIVERGÊNCIA DE NASCIMENTO")
                    
                    if tipo == "EDUC":
                        if cpf_atual not in old_data[tipo][nome]['CPF']: inconsistencias.append(f"DIVERGÊNCIA DE CPF")

                if inconsistencias:
                    # Tag de identificação para o relatório
                    inconsistencias = [f"[{tipo}] {erro}" for erro in inconsistencias]
                    nome_formatado = str(row.get('NOME DO SEGURADO', '')).strip()
                    cpf_relatorio = str(row.get('CPF', '')).strip() if tipo == "EDUC" else "N/A (Regra AP)"
                    erros_totais[(nome_formatado, cpf_relatorio)] = inconsistencias
                    if tipo == "AP": cont_ap += 1
                    else: cont_educ += 1

            self.progress.set(1.0)
            self.exibir_resultado_animado(cont_ap, cont_educ)
            self.exportar_relatorio_estilizado(erros_totais)

        except Exception as e:
            self.animar_texto(self.lbl_status, "ERRO CRÍTICO NO PROCESSAMENTO.", "#FF4D4D")
            messagebox.showerror("Erro", str(e))

    def exibir_resultado_animado(self, ap, educ):
        total = ap + educ
        esperado_str = self.entry_erros.get().strip()
        
        msg = f"Encontrados: {total} erros (AP: {ap} | EDUC: {educ})"
        
        if esperado_str.isdigit():
            esperado = int(esperado_str)
            if total == esperado:
                self.animar_texto(self.lbl_status, f"{msg} ➜ ✅ BATEU EXATAMENTE!", "#00FF7F")
            else:
                self.animar_texto(self.lbl_status, f"{msg} ➜ ❌ DIVERGIU DO SISTEMA ({esperado})", "#FF4D4D")
        else:
            self.animar_texto(self.lbl_status, msg + " ➜ ✔️ CONCLUÍDO", "#3498db")

    def exportar_relatorio_estilizado(self, erros_dict):
        if not erros_dict:
            messagebox.showinfo("Sucesso", "Nenhuma divergência encontrada. Os dados estão perfeitos!")
            return

        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Planilha Excel", "*.xlsx")], initialfile="Auditoria_Premium.xlsx")
        if not path: return
        
        try:
            # Prepara os dados
            dados = []
            for (nome, cpf), lista_erros in erros_dict.items():
                linha = {"SEGURADO": nome, "CPF": cpf}
                for i, erro in enumerate(lista_erros):
                    linha[f"INCONSISTÊNCIA {i+1}"] = erro
                dados.append(linha)
                
            df = pd.DataFrame(dados)
            
            # Exporta via Pandas
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Auditoria')
                
                # Estilização Deluxe via Openpyxl
                workbook = writer.book
                worksheet = writer.sheets['Auditoria']
                
                from openpyxl.styles import PatternFill, Font, Alignment
                
                header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                align = Alignment(horizontal="center", vertical="center")
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = align
                
                for col in worksheet.columns:
                    max_length = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length: max_length = len(cell.value)
                        except: pass
                    adjusted_width = (max_length + 3)
                    worksheet.column_dimensions[col_letter].width = adjusted_width
            
            messagebox.showinfo("Exportado", "Relatório estilizado gerado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro de Exportação", f"Não foi possível salvar e formatar a planilha:\n{str(e)}")

if __name__ == "__main__":
    app = AuditorSeguradosPro()
    app.mainloop()
