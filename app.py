import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import os
import re

# ==========================================
# CONFIGURAÇÃO DE DESIGN DELUXE & SLIM
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue") 

class HubUtilitarios(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hub Analítico de Segurados")
        self.geometry("500x550")
        self.resizable(False, False)
        
        self.tabview = ctk.CTkTabview(self, corner_radius=8, border_width=0)
        self.tabview.pack(padx=15, pady=10, fill="both", expand=True)
        
        self.tab_auditor = self.tabview.add("🔍 Auditoria de Divergências")
        self.tab_mapeador = self.tabview.add("📊 Mapeador Analítico (PROCV)")
        
        self.configurar_auditor()
        self.configurar_mapeador()

        self.lbl_footer = ctk.CTkLabel(self, text="Desenvolvido por Matheus Carvalho", font=("Segoe UI", 10, "italic"), text_color="#555555")
        self.lbl_footer.pack(side="bottom", pady=5)

    # ==========================================
    # ABA 1: AUDITORIA (AP / EDUC / AMBOS)
    # ==========================================
    def configurar_auditor(self):
        self.arq_atuais = []
        self.arq_anteriores = []
        
        self.frame_uploads = ctk.CTkFrame(self.tab_auditor, fg_color="transparent")
        self.frame_uploads.pack(pady=20, fill="x")

        self.btn_atuais = ctk.CTkButton(self.frame_uploads, text="📁 Selecionar Planilhas ATUAIS", 
                                        command=self.selecionar_atuais, width=300, height=35, 
                                        fg_color="#2c2c2e", hover_color="#3a3a3c", border_width=1, border_color="#444")
        self.btn_atuais.pack(pady=5)
        self.lbl_atuais = ctk.CTkLabel(self.frame_uploads, text="Nenhum arquivo selecionado", text_color="#888888", font=("Segoe UI", 11))
        self.lbl_atuais.pack(pady=(0, 10))

        self.btn_anteriores = ctk.CTkButton(self.frame_uploads, text="📁 Selecionar Planilhas ANTERIORES", 
                                            command=self.selecionar_anteriores, width=300, height=35, 
                                            fg_color="#2c2c2e", hover_color="#3a3a3c", border_width=1, border_color="#444")
        self.btn_anteriores.pack(pady=5)
        self.lbl_anteriores = ctk.CTkLabel(self.frame_uploads, text="Nenhum arquivo selecionado", text_color="#888888", font=("Segoe UI", 11))
        self.lbl_anteriores.pack()

        ctk.CTkFrame(self.tab_auditor, height=1, fg_color="#333").pack(fill="x", padx=40, pady=15)

        self.entry_erros = ctk.CTkEntry(self.tab_auditor, placeholder_text="Qtd. de Erros no Sistema (Opcional)", 
                                        width=250, justify="center", border_width=1, fg_color="#1c1c1e")
        self.entry_erros.pack(pady=10)

        self.btn_exec_auditor = ctk.CTkButton(self.tab_auditor, text="⚡ Iniciar Auditoria", command=self.iniciar_auditoria, 
                                              fg_color="#005A9E", hover_color="#004070", font=("Segoe UI", 13, "bold"), height=40, width=250)
        self.btn_exec_auditor.pack(pady=10)

        self.progress_auditor = ctk.CTkProgressBar(self.tab_auditor, width=350, height=4, progress_color="#005A9E")
        self.progress_auditor.pack(pady=10)
        self.progress_auditor.set(0)

        self.lbl_relatorio = ctk.CTkLabel(self.tab_auditor, text="", font=("Segoe UI", 12), text_color="#AAAAAA", justify="center")
        self.lbl_relatorio.pack(pady=5)

    def selecionar_atuais(self):
        arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos", "*.txt *.csv *.TXT *.xlsx")])
        if arquivos:
            self.arq_atuais = arquivos
            self.lbl_atuais.configure(text=f"{len(arquivos)} arquivo(s) carregado(s)", text_color="#00FF7F")

    def selecionar_anteriores(self):
        arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos", "*.txt *.csv *.TXT *.xlsx")])
        if arquivos:
            self.arq_anteriores = arquivos
            self.lbl_anteriores.configure(text=f"{len(arquivos)} arquivo(s) carregado(s)", text_color="#00FF7F")

    def iniciar_auditoria(self):
        if not self.arq_atuais or not self.arq_anteriores:
            messagebox.showwarning("Aviso", "Por favor, carregue os arquivos.")
            return
        self.btn_exec_auditor.configure(state="disabled")
        self.progress_auditor.set(0.1)
        self.lbl_relatorio.configure(text="Analisando cruzamentos...", text_color="#F1C40F")
        threading.Thread(target=self.processar_auditoria).start()

    def processar_auditoria(self):
        try:
            df_atual = self.compilar_dados(self.arq_atuais)
            df_conf = self.compilar_dados(self.arq_anteriores)
            self.progress_auditor.set(0.4)
            
            old_data = {'AP': {}, 'EDUC': {}}
            
            for _, row in df_conf.iterrows():
                tipo = row['TIPO']
                nome = str(row.get('NOME DO SEGURADO', '')).strip().upper()
                if not nome: continue
                
                if nome not in old_data[tipo]:
                    old_data[tipo][nome] = {'MAT': [], 'CERT': [], 'CPF': [], 'NASC': []}
                
                old_data[tipo][nome]['MAT'].append(str(row.get('MATRICULA', '')).strip().upper())
                old_data[tipo][nome]['CERT'].append(str(row.get('CERTIFICADO', '')).strip().upper())
                old_data[tipo][nome]['CPF'].append(str(row.get('CPF', '')).strip().upper())
                old_data[tipo][nome]['NASC'].append(str(row.get('DATA DE NASCIMENTO', '')).strip().upper())

            self.progress_auditor.set(0.6)
            
            erros_totais = {}
            cont_ap = 0
            cont_educ = 0
            total_linhas = len(df_atual)

            for idx, row in df_atual.iterrows():
                if idx % 50 == 0:
                    self.progress_auditor.set(0.6 + (0.3 * (idx / total_linhas)))
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
                    inconsistencias.append("NÃO ENCONTRADO NA PLANILHA ANTERIOR")
                else:
                    if mat_atual not in old_data[tipo][nome]['MAT']:
                        inconsistencias.append(f"MATRÍCULA (Atual: {mat_atual} | Antigas: {', '.join(set(old_data[tipo][nome]['MAT']))})")
                    if cert_atual not in old_data[tipo][nome]['CERT']:
                        inconsistencias.append(f"CERTIFICADO (Atual: {cert_atual} | Antigos: {', '.join(set(old_data[tipo][nome]['CERT']))})")
                    if nasc_atual not in old_data[tipo][nome]['NASC']:
                        inconsistencias.append(f"NASCIMENTO (Atual: {nasc_atual} | Antigos: {', '.join(set(old_data[tipo][nome]['NASC']))})")
                    
                    # Retornado ao padrão: Apenas EDUC valida o CPF
                    if tipo == "EDUC":
                        if cpf_atual not in old_data[tipo][nome]['CPF']:
                            inconsistencias.append(f"CPF (Atual: {cpf_atual} | Antigos: {', '.join(set(old_data[tipo][nome]['CPF']))})")

                if inconsistencias:
                    inconsistencias = [f"[{tipo}] {erro}" for erro in inconsistencias]
                    nome_formatado = str(row.get('NOME DO SEGURADO', '')).strip()
                    # No relatório, o CPF é omitido se for AP, pois não é validado
                    cpf_relatorio = str(row.get('CPF', '')).strip() if tipo == "EDUC" else "N/A (Modo AP)"
                    erros_totais[(nome_formatado, cpf_relatorio)] = inconsistencias
                    
                    if tipo == "AP": cont_ap += 1
                    else: cont_educ += 1

            self.progress_auditor.set(1.0)
            self.atualizar_interface_relatorio(cont_ap, cont_educ)
            self.gerar_planilha_auditoria(erros_totais)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha na auditoria:\n{str(e)}")
            self.lbl_relatorio.configure(text="Erro crítico no processamento.", text_color="#FF4D4D")
        finally:
            self.btn_exec_auditor.configure(state="normal")
            self.progress_auditor.set(0)

    def atualizar_interface_relatorio(self, ap, educ):
        total = ap + educ
        esperado_str = self.entry_erros.get().strip()
        
        texto = f"Resultados: AP ({ap}) | EDUC ({educ}) | Total Geral ({total})"
        cor = "#FFFFFF"

        if esperado_str.isdigit():
            esperado = int(esperado_str)
            if total == esperado:
                texto += f"\n\nSistema acusou {esperado} -> ✅ BATEU EXATAMENTE!"
                cor = "#00FF7F"
            else:
                texto += f"\n\nSistema acusou {esperado} -> ❌ HÁ DIVERGÊNCIA!"
                cor = "#FF4D4D"

        self.lbl_relatorio.configure(text=texto, text_color=cor)

    def gerar_planilha_auditoria(self, erros_dict):
        if not erros_dict:
            messagebox.showinfo("Sucesso", "Nenhuma divergência encontrada! Os dados estão perfeitos.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")], initialfile="Relatorio_Auditoria.xlsx")
        if not path: return
        
        try:
            dados = []
            for (nome, cpf), lista_erros in erros_dict.items():
                linha = {"Nome do Segurado": nome, "CPF": cpf}
                for i, erro in enumerate(lista_erros):
                    linha[f"Erro {i+1}"] = erro
                dados.append(linha)
                
            df = pd.DataFrame(dados)
            if path.endswith('.csv'): df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')
            else: df.to_excel(path, index=False)
            messagebox.showinfo("Exportado", "Relatório de divergências gerado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")


    # ==========================================
    # ABA 2: MAPEADOR ANALÍTICO (PROCV)
    # ==========================================
    def configurar_mapeador(self):
        self.arq_alvo_map = ""
        self.arq_base_map = ""
        
        self.frame_uploads_map = ctk.CTkFrame(self.tab_mapeador, fg_color="transparent")
        self.frame_uploads_map.pack(pady=10, fill="x")
        
        self.btn_alvo_map = ctk.CTkButton(self.frame_uploads_map, text="📂 1. Planilha ALVO (Que receberá a coluna)", 
                                          command=self.selecionar_alvo_map, width=300, height=35, fg_color="#2c2c2e", hover_color="#3a3a3c", border_width=1, border_color="#444")
        self.btn_alvo_map.pack(pady=5)
        self.lbl_alvo_map = ctk.CTkLabel(self.frame_uploads_map, text="Nenhum arquivo", text_color="#888")
        self.lbl_alvo_map.pack(pady=(0, 5))

        self.btn_base_map = ctk.CTkButton(self.frame_uploads_map, text="📂 2. Planilha BASE (Onde os dados estão)", 
                                          command=self.selecionar_base_map, width=300, height=35, fg_color="#2c2c2e", hover_color="#3a3a3c", border_width=1, border_color="#444")
        self.btn_base_map.pack(pady=5)
        self.lbl_base_map = ctk.CTkLabel(self.frame_uploads_map, text="Nenhum arquivo", text_color="#888")
        self.lbl_base_map.pack()

        self.frame_configs = ctk.CTkFrame(self.tab_mapeador, fg_color="#1c1c1e", corner_radius=5)
        self.frame_configs.pack(pady=10, padx=20, fill="x")
        
        self.lbl_conf_alvo = ctk.CTkLabel(self.frame_configs, text="Chave de Busca (ALVO):", font=("Segoe UI", 12))
        self.lbl_conf_alvo.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.combo_chave_alvo = ctk.CTkOptionMenu(self.frame_configs, values=["Carregue a planilha"], width=150)
        self.combo_chave_alvo.grid(row=0, column=1, padx=10, pady=10)

        self.lbl_conf_base = ctk.CTkLabel(self.frame_configs, text="Chave de Busca (BASE):", font=("Segoe UI", 12))
        self.lbl_conf_base.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.combo_chave_base = ctk.CTkOptionMenu(self.frame_configs, values=["Carregue a planilha"], width=150)
        self.combo_chave_base.grid(row=1, column=1, padx=10, pady=10)

        self.lbl_conf_imp = ctk.CTkLabel(self.frame_configs, text="Coluna a IMPORTAR:", font=("Segoe UI", 12))
        self.lbl_conf_imp.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.combo_importar = ctk.CTkOptionMenu(self.frame_configs, values=["Carregue a planilha"], width=150)
        self.combo_importar.grid(row=2, column=1, padx=10, pady=10)

        self.check_limpar = ctk.CTkCheckBox(self.tab_mapeador, text="Limpar pontuações da Chave (Ideal para CPF/CNPJ)")
        self.check_limpar.pack(pady=10)

        self.btn_exec_map = ctk.CTkButton(self.tab_mapeador, text="⚡ Importar Coluna", command=self.iniciar_thread_map, 
                                          fg_color="#005A9E", hover_color="#004070", font=("Segoe UI", 13, "bold"), height=40, width=250)
        self.btn_exec_map.pack(pady=10)
        
        self.progress_map = ctk.CTkProgressBar(self.tab_mapeador, width=350, height=4, progress_color="#005A9E")
        self.progress_map.pack(pady=10)
        self.progress_map.set(0)

    def extrair_colunas(self, caminho):
        if caminho.lower().endswith(('.xlsx', '.xls')): df = pd.read_excel(caminho, nrows=0)
        else:
            try: df = pd.read_csv(caminho, sep=';', nrows=0, encoding='utf-8-sig')
            except: df = pd.read_csv(caminho, sep=';', nrows=0, encoding='latin-1')
        return list(df.columns)

    def selecionar_alvo_map(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos", "*.xlsx *.csv *.txt *.TXT")])
        if caminho:
            self.arq_alvo_map = caminho
            self.lbl_alvo_map.configure(text=os.path.basename(caminho), text_color="#00FF7F")
            colunas = self.extrair_colunas(caminho)
            if colunas:
                self.combo_chave_alvo.configure(values=colunas)
                self.combo_chave_alvo.set(colunas[0])

    def selecionar_base_map(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos", "*.xlsx *.csv *.txt *.TXT")])
        if caminho:
            self.arq_base_map = caminho
            self.lbl_base_map.configure(text=os.path.basename(caminho), text_color="#00FF7F")
            colunas = self.extrair_colunas(caminho)
            if colunas:
                self.combo_chave_base.configure(values=colunas)
                self.combo_importar.configure(values=colunas)
                self.combo_chave_base.set(colunas[0])
                self.combo_importar.set(colunas[0])

    def iniciar_thread_map(self):
        if not self.arq_alvo_map or not self.arq_base_map:
            messagebox.showwarning("Aviso", "Selecione as duas planilhas.")
            return
        self.btn_exec_map.configure(state="disabled")
        self.progress_map.set(0.1)
        threading.Thread(target=self.processar_mapeador).start()

    def processar_mapeador(self):
        try:
            df_alvo = self.ler_arquivo(self.arq_alvo_map)
            df_base = self.ler_arquivo(self.arq_base_map)
            self.progress_map.set(0.4)

            ch_alvo = self.combo_chave_alvo.get()
            ch_base = self.combo_chave_base.get()
            col_imp = self.combo_importar.get()
            limpar = self.check_limpar.get() == 1

            mapa = {}
            for _, row in df_base.iterrows():
                k = str(row[ch_base]).strip()
                if limpar: k = re.sub(r'\D', '', k)
                v = str(row[col_imp]).strip()
                if k: mapa[k] = v

            self.progress_map.set(0.7)

            novos_valores = []
            for _, row in df_alvo.iterrows():
                k = str(row[ch_alvo]).strip()
                if limpar: k = re.sub(r'\D', '', k)
                novos_valores.append(mapa.get(k, "NÃO LOCALIZADO"))

            df_alvo.insert(0, f"IMP_{col_imp}", novos_valores)
            self.progress_map.set(1.0)
            
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")], initialfile=f"Planilha_PROCV.xlsx")
            if path:
                if path.endswith('.csv'): df_alvo.to_csv(path, index=False, sep=';', encoding='utf-8-sig')
                else: df_alvo.to_excel(path, index=False)
                messagebox.showinfo("Sucesso", f"A coluna '{col_imp}' foi adicionada!")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha na importação:\n{str(e)}")
        finally:
            self.btn_exec_map.configure(state="normal")
            self.progress_map.set(0)

    # ==========================================
    # UTILITÁRIOS GERAIS DE ARQUIVO
    # ==========================================
    def ler_arquivo(self, caminho):
        if caminho.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(caminho, dtype=str).fillna("")
        else:
            try: return pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig').fillna("")
            except: return pd.read_csv(caminho, sep=';', dtype=str, encoding='latin-1').fillna("")

    def compilar_dados(self, arquivos):
        lista = []
        for caminho in arquivos:
            df = self.ler_arquivo(caminho)
            df['TIPO'] = "EDUC" if "EDUC" in os.path.basename(caminho).upper() else "AP"
            lista.append(df)
        return pd.concat(lista, ignore_index=True) if lista else pd.DataFrame()

if __name__ == "__main__":
    app = HubUtilitarios()
    app.mainloop()
