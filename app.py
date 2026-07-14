import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import threading

# Layout Minimalista Moderno
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ComparadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Comparador de Segurados v6.0")
        self.geometry("600x700")
        self.resizable(False, False)
        
        # Variáveis de arquivos
        self.arq_ap_atual = []
        self.arq_ap_conf = []
        self.arq_educ_atual = []
        self.arq_educ_conf = []
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=15, padx=15, fill="both", expand=True)

        self.lbl_title = ctk.CTkLabel(self.main_frame, text="Verificador de Inconsistências", font=("Roboto", 20, "bold"))
        self.lbl_title.pack(pady=(15, 10))
        
        # Seletor de Modo
        self.modo_var = ctk.StringVar(value="EDUC")
        self.seg_modo = ctk.CTkSegmentedButton(self.main_frame, values=["AP", "EDUC", "AMBOS"], 
                                               variable=self.modo_var, font=("Roboto", 12), command=self.mudar_modo)
        self.seg_modo.pack(pady=(0, 15))

        # --- BLOCO AP ---
        self.frame_ap = ctk.CTkFrame(self.main_frame, fg_color="#1e3d59", corner_radius=8)
        self.lbl_ap_title = ctk.CTkLabel(self.frame_ap, text="Arquivos AP", font=("Roboto", 14, "bold"), text_color="white")
        self.lbl_ap_title.pack(pady=(5, 0))
        
        self.btn_ap_atual = ctk.CTkButton(self.frame_ap, text="📂 1. AP: Planilha Atual", command=lambda: self.selecionar_arq('ap_atual'), width=250)
        self.btn_ap_atual.pack(pady=(10, 2))
        self.lbl_ap_atual = ctk.CTkLabel(self.frame_ap, text="Nenhum arquivo", text_color="lightgray", font=("Roboto", 11))
        self.lbl_ap_atual.pack(pady=(0, 5))
        
        self.btn_ap_conf = ctk.CTkButton(self.frame_ap, text="📂 2. AP: Planilha Anterior", command=lambda: self.selecionar_arq('ap_conf'), width=250)
        self.btn_ap_conf.pack(pady=(5, 2))
        self.lbl_ap_conf = ctk.CTkLabel(self.frame_ap, text="Nenhum arquivo", text_color="lightgray", font=("Roboto", 11))
        self.lbl_ap_conf.pack(pady=(0, 10))

        # --- BLOCO EDUC ---
        self.frame_educ = ctk.CTkFrame(self.main_frame, fg_color="#432c54", corner_radius=8)
        self.lbl_educ_title = ctk.CTkLabel(self.frame_educ, text="Arquivos EDUC", font=("Roboto", 14, "bold"), text_color="white")
        self.lbl_educ_title.pack(pady=(5, 0))
        
        self.btn_educ_atual = ctk.CTkButton(self.frame_educ, text="📂 1. EDUC: Planilha Atual", command=lambda: self.selecionar_arq('educ_atual'), width=250)
        self.btn_educ_atual.pack(pady=(10, 2))
        self.lbl_educ_atual = ctk.CTkLabel(self.frame_educ, text="Nenhum arquivo", text_color="lightgray", font=("Roboto", 11))
        self.lbl_educ_atual.pack(pady=(0, 5))
        
        self.btn_educ_conf = ctk.CTkButton(self.frame_educ, text="📂 2. EDUC: Planilha Anterior", command=lambda: self.selecionar_arq('educ_conf'), width=250)
        self.btn_educ_conf.pack(pady=(5, 2))
        self.lbl_educ_conf = ctk.CTkLabel(self.frame_educ, text="Nenhum arquivo", text_color="lightgray", font=("Roboto", 11))
        self.lbl_educ_conf.pack(pady=(0, 10))

        # Exibir bloco inicial
        self.mudar_modo("EDUC")

        # Input de Erros do Sistema
        self.entry_erros = ctk.CTkEntry(self.main_frame, placeholder_text="Qtd. Erros no Sistema (Opcional)", width=220, justify="center")
        self.entry_erros.pack(pady=(15, 5))

        # Barra de Progresso
        self.progress = ctk.CTkProgressBar(self.main_frame, width=450, height=10)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        # Botão Executar
        self.btn_executar = ctk.CTkButton(self.main_frame, text="⚡ Processar e Gerar Relatório", command=self.iniciar_thread_verificacao, 
                                          fg_color="#006400", hover_color="#004d00", font=("Roboto", 14, "bold"), height=40)
        self.btn_executar.pack(pady=10, padx=30, fill="x")

        # Mini Relatório
        self.frame_relatorio = ctk.CTkFrame(self.main_frame, fg_color="#2b2b2b", corner_radius=5)
        self.frame_relatorio.pack(pady=(0, 10), padx=20, fill="x")
        self.lbl_relatorio = ctk.CTkLabel(self.frame_relatorio, text="Aguardando processamento...", font=("Roboto", 12), text_color="white", justify="center")
        self.lbl_relatorio.pack(pady=10, padx=10)

        # Rodapé
        self.lbl_footer = ctk.CTkLabel(self, text="Criado por Matheus Carvalho", font=("Roboto", 10, "italic"), text_color="gray")
        self.lbl_footer.pack(side="bottom", pady=5)

    def mudar_modo(self, modo):
        if modo == "AP":
            self.frame_educ.pack_forget()
            self.frame_ap.pack(pady=5, padx=20, fill="x")
        elif modo == "EDUC":
            self.frame_ap.pack_forget()
            self.frame_educ.pack(pady=5, padx=20, fill="x")
        elif modo == "AMBOS":
            self.frame_ap.pack(pady=5, padx=20, fill="x")
            self.frame_educ.pack(pady=5, padx=20, fill="x")

    def selecionar_arq(self, tipo):
        arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos", "*.txt *.csv *.TXT")])
        if arquivos:
            texto = f"{len(arquivos)} arquivo(s) selecionado(s)"
            if tipo == 'ap_atual':
                self.arq_ap_atual = arquivos
                self.lbl_ap_atual.configure(text=texto, text_color="white")
            elif tipo == 'ap_conf':
                self.arq_ap_conf = arquivos
                self.lbl_ap_conf.configure(text=texto, text_color="white")
            elif tipo == 'educ_atual':
                self.arq_educ_atual = arquivos
                self.lbl_educ_atual.configure(text=texto, text_color="white")
            elif tipo == 'educ_conf':
                self.arq_educ_conf = arquivos
                self.lbl_educ_conf.configure(text=texto, text_color="white")

    def ler_arquivo(self, caminho):
        try:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig').fillna("")
        except UnicodeDecodeError:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='latin-1').fillna("")

    def compilar_dados(self, arquivos):
        lista_dfs = []
        for caminho in arquivos:
            lista_dfs.append(self.ler_arquivo(caminho))
        return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

    def iniciar_thread_verificacao(self):
        self.btn_executar.configure(state="disabled", text="Processando...")
        self.lbl_relatorio.configure(text="Analisando dados...", text_color="yellow")
        self.progress.set(0)
        threading.Thread(target=self.processar_planilhas).start()

    def processar_planilhas(self):
        try:
            modo = self.modo_var.get()
            erros_totais = {}
            cont_ap = 0
            cont_educ = 0

            # Processamento AP
            if modo in ["AP", "AMBOS"] and self.arq_ap_atual and self.arq_ap_conf:
                df_atual_ap = self.compilar_dados(self.arq_ap_atual)
                df_conf_ap = self.compilar_dados(self.arq_ap_conf)
                erros_ap, qtd = self.analisar_bloco(df_atual_ap, df_conf_ap, "AP")
                erros_totais.update(erros_ap)
                cont_ap = qtd

            # Processamento EDUC
            if modo in ["EDUC", "AMBOS"] and self.arq_educ_atual and self.arq_educ_conf:
                df_atual_educ = self.compilar_dados(self.arq_educ_atual)
                df_conf_educ = self.compilar_dados(self.arq_educ_conf)
                erros_educ, qtd = self.analisar_bloco(df_atual_educ, df_conf_educ, "EDUC")
                erros_totais.update(erros_educ)
                cont_educ = qtd

            self.atualizar_relatorio_interface(cont_ap, cont_educ, modo)
            self.gerar_planilha(erros_totais)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar:\n{str(e)}")
            self.lbl_relatorio.configure(text="Erro no processamento.", text_color="red")
        finally:
            self.btn_executar.configure(state="normal", text="⚡ Processar e Gerar Relatório")
            self.progress.set(1)

    def analisar_bloco(self, df_atual, df_conf, tipo_regra):
        erros_dict = {}
        cont_erros = 0
        total_linhas = len(df_atual)

        for idx, row in df_atual.iterrows():
            self.progress.set((idx + 1) / total_linhas)
            self.update_idletasks()
            
            nome = str(row.get('NOME DO SEGURADO', '')).strip()
            if not nome: continue

            cpf_atual = str(row.get('CPF', '')).strip()
            nasc_atual = str(row.get('DATA DE NASCIMENTO', '')).strip()
            mat_atual = str(row.get('MATRICULA', '')).strip()
            cert_atual = str(row.get('CERTIFICADO', '')).strip()
            
            # Encontra todas as linhas com esse nome na planilha de conferência
            matches = df_conf[df_conf['NOME DO SEGURADO'].str.strip() == nome]
            cpf_relatorio = cpf_atual if tipo_regra == "EDUC" else "N/A (Modo AP)"
            
            if matches.empty:
                erros_dict[(nome, cpf_relatorio)] = [f"[{tipo_regra}] NÃO ENCONTRADO NA PLANILHA ANTERIOR"]
                cont_erros += 1
                continue
            
            # LÓGICA INTELIGENTE PARA NOMES REPETIDOS (Filhos da mesma pessoa no EDUC)
            if len(matches) == 1:
                row_conf = matches.iloc[0]
            else:
                # Se achou mais de um, usa a Matrícula para descobrir qual é o filho correto
                match_matricula = matches[matches['MATRICULA'].str.strip() == mat_atual]
                if not match_matricula.empty:
                    row_conf = match_matricula.iloc[0]
                else:
                    # Se não bateu a matrícula, tenta pelo certificado
                    match_cert = matches[matches['CERTIFICADO'].str.strip() == cert_atual]
                    if not match_cert.empty:
                        row_conf = match_cert.iloc[0]
                    else:
                        # Se tudo falhar, pega o primeiro para acusar a divergência geral
                        row_conf = matches.iloc[0]

            nome_conf = str(row_conf.get('NOME DO SEGURADO', '')).strip()
            cpf_conf = str(row_conf.get('CPF', '')).strip()
            nasc_conf = str(row_conf.get('DATA DE NASCIMENTO', '')).strip()
            mat_conf = str(row_conf.get('MATRICULA', '')).strip()
            cert_conf = str(row_conf.get('CERTIFICADO', '')).strip()
            
            inconsistencias = []
            
            # Comparações (Simulando seus Concats)
            if mat_atual != mat_conf:
                inconsistencias.append(f"MATRÍCULA (Atual: {mat_atual} -> Conf: {mat_conf})")
            if cert_atual != cert_conf:
                inconsistencias.append(f"CERTIFICADO (Atual: {cert_atual} -> Conf: {cert_conf})")
            if nasc_atual != nasc_conf:
                inconsistencias.append(f"NASCIMENTO (Atual: {nasc_atual} -> Conf: {nasc_conf})")
                
            if tipo_regra == "EDUC":
                if cpf_atual != cpf_conf:
                    inconsistencias.append(f"CPF (Atual: {cpf_atual} -> Conf: {cpf_conf})")
                    
            if inconsistencias:
                # Adiciona uma tag indicando a origem (AP ou EDUC)
                inconsistencias = [f"[{tipo_regra}] " + erro for erro in inconsistencias]
                erros_dict[(nome, cpf_relatorio)] = inconsistencias
                cont_erros += 1

        return erros_dict, cont_erros

    def atualizar_relatorio_interface(self, ap, educ, modo):
        total_encontrado = ap + educ
        esperado_str = self.entry_erros.get().strip()
        
        texto_base = ""
        if modo == "AP":
            texto_base = f"Total Identificado (AP): {ap}"
        elif modo == "EDUC":
            texto_base = f"Total Identificado (EDUC): {educ}"
        else:
            texto_base = f"AP: {ap} | EDUC: {educ} | Total Geral: {total_encontrado}"
            
        cor_texto = "#00FF00" # Verde
        
        if esperado_str.isdigit():
            esperado = int(esperado_str)
            if total_encontrado == esperado:
                texto_base += f"\nSistema ({esperado}) -> ✅ BATEU PERFEITAMENTE!"
            else:
                texto_base += f"\nSistema ({esperado}) -> ❌ DIVERGIU!"
                cor_texto = "#FF4500" # Vermelho
                
        self.lbl_relatorio.configure(text=texto_base, text_color=cor_texto)

    def gerar_planilha(self, erros_dict):
        if not erros_dict:
            messagebox.showinfo("Sucesso", "Nenhum erro encontrado! As planilhas batem perfeitamente.")
            return

        planilha_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Planilha do Excel", "*.xlsx"), ("Arquivo CSV", "*.csv")], 
            initialfile="Inconsistencias.xlsx"
        )
        
        if not planilha_path:
            return
        
        try:
            dados_planilha = []
            for (nome, cpf_relatorio), lista_erros in erros_dict.items():
                linha = {"Nome do Segurado": nome, "CPF": cpf_relatorio}
                for i, erro in enumerate(lista_erros):
                    linha[f"Erro {i+1}"] = erro
                dados_planilha.append(linha)
                
            df_relatorio = pd.DataFrame(dados_planilha)
            
            if planilha_path.endswith('.csv'):
                df_relatorio.to_csv(planilha_path, index=False, sep=';', encoding='utf-8-sig')
            else:
                df_relatorio.to_excel(planilha_path, index=False)
                
            messagebox.showinfo("Sucesso", "Planilha salva com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")

if __name__ == "__main__":
    app = ComparadorApp()
    app.mainloop()
