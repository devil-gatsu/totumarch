import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import os

# Layout Minimalista Moderno
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ComparadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Comparador de Segurados v5.0")
        self.geometry("550x620")
        self.resizable(False, False)
        
        self.arquivos_atuais = []
        self.arquivos_conferidos = []
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=15, padx=15, fill="both", expand=True)

        self.lbl_title = ctk.CTkLabel(self.main_frame, text="Verificador de Inconsistências", font=("Roboto", 20, "bold"))
        self.lbl_title.pack(pady=(15, 10))
        
        # Seletor de Modo
        self.modo_var = ctk.StringVar(value="EDUC")
        self.seg_modo = ctk.CTkSegmentedButton(self.main_frame, values=["AP", "EDUC", "AMBOS"], variable=self.modo_var, font=("Roboto", 12))
        self.seg_modo.pack(pady=(0, 15))

        # Botões de Arquivo (Agora suporta múltiplos arquivos)
        self.btn_atual = ctk.CTkButton(self.main_frame, text="📂 1. Selecionar Planilha(s) Atual(is)", command=self.selecionar_atual, height=35, width=300)
        self.btn_atual.pack(pady=(5, 2))
        self.lbl_atual = ctk.CTkLabel(self.main_frame, text="Nenhum arquivo", text_color="gray", font=("Roboto", 11))
        self.lbl_atual.pack(pady=(0, 10))
        
        self.btn_conferido = ctk.CTkButton(self.main_frame, text="📂 2. Selecionar Planilha(s) Anterior(es)", command=self.selecionar_conferida, height=35, width=300)
        self.btn_conferido.pack(pady=(5, 2))
        self.lbl_conferido = ctk.CTkLabel(self.main_frame, text="Nenhum arquivo", text_color="gray", font=("Roboto", 11))
        self.lbl_conferido.pack(pady=(0, 15))

        # Input de Erros do Sistema
        self.entry_erros = ctk.CTkEntry(self.main_frame, placeholder_text="Qtd. Erros no Sistema (Opcional)", width=220, justify="center")
        self.entry_erros.pack(pady=(0, 15))

        # Barra de Progresso
        self.progress = ctk.CTkProgressBar(self.main_frame, width=450, height=10)
        self.progress.pack(pady=(5, 15))
        self.progress.set(0)
        
        # Botão Executar
        self.btn_executar = ctk.CTkButton(self.main_frame, text="⚡ Processar e Gerar Relatório", command=self.iniciar_thread_verificacao, 
                                          fg_color="#006400", hover_color="#004d00", font=("Roboto", 14, "bold"), height=40)
        self.btn_executar.pack(pady=(0, 15), padx=30, fill="x")

        # Mini Relatório
        self.frame_relatorio = ctk.CTkFrame(self.main_frame, fg_color="#2b2b2b", corner_radius=5)
        self.frame_relatorio.pack(pady=(0, 10), padx=20, fill="x")
        self.lbl_relatorio = ctk.CTkLabel(self.frame_relatorio, text="Aguardando processamento...", font=("Roboto", 12), text_color="white", justify="center")
        self.lbl_relatorio.pack(pady=10, padx=10)

        # Rodapé
        self.lbl_footer = ctk.CTkLabel(self, text="Criado por Matheus Carvalho", font=("Roboto", 10, "italic"), text_color="gray")
        self.lbl_footer.pack(side="bottom", pady=5)

    def selecionar_atual(self):
        self.arquivos_atuais = filedialog.askopenfilenames(filetypes=[("Arquivos", "*.txt *.csv *.TXT")])
        if self.arquivos_atuais:
            self.lbl_atual.configure(text=f"{len(self.arquivos_atuais)} arquivo(s) selecionado(s)", text_color="white")

    def selecionar_conferida(self):
        self.arquivos_conferidos = filedialog.askopenfilenames(filetypes=[("Arquivos", "*.txt *.csv *.TXT")])
        if self.arquivos_conferidos:
            self.lbl_conferido.configure(text=f"{len(self.arquivos_conferidos)} arquivo(s) selecionado(s)", text_color="white")

    def ler_arquivo(self, caminho):
        try:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig').fillna("")
        except UnicodeDecodeError:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='latin-1').fillna("")

    def compilar_dados(self, arquivos, modo):
        lista_dfs = []
        for caminho in arquivos:
            df = self.ler_arquivo(caminho)
            # Define a regra com base no nome do arquivo se for modo AMBOS
            if modo == "AMBOS":
                regra = "EDUC" if "EDUC" in os.path.basename(caminho).upper() else "AP"
            else:
                regra = modo
            df['TIPO_REGRA'] = regra
            lista_dfs.append(df)
        
        if lista_dfs:
            return pd.concat(lista_dfs, ignore_index=True)
        return pd.DataFrame()

    def iniciar_thread_verificacao(self):
        if not self.arquivos_atuais or not self.arquivos_conferidos:
            messagebox.showwarning("Aviso", "Selecione as planilhas atuais e as anteriores.")
            return
        
        self.btn_executar.configure(state="disabled", text="Processando...")
        self.lbl_relatorio.configure(text="Analisando dados...", text_color="yellow")
        self.progress.set(0)
        threading.Thread(target=self.processar_planilhas).start()

    def processar_planilhas(self):
        try:
            modo = self.modo_var.get()
            
            # Junta todos os arquivos selecionados em um grande bloco para análise
            df_atual = self.compilar_dados(self.arquivos_atuais, modo)
            df_conferida = self.compilar_dados(self.arquivos_conferidos, modo)
            
            erros_dict = {}
            total_linhas = len(df_atual)
            
            cont_erros_ap = 0
            cont_erros_educ = 0
            
            for idx, row in df_atual.iterrows():
                self.progress.set((idx + 1) / total_linhas)
                self.update_idletasks()
                
                nome = str(row.get('NOME DO SEGURADO', '')).strip()
                if not nome:
                    continue

                cpf_atual = str(row.get('CPF', '')).strip()
                nasc_atual = str(row.get('DATA DE NASCIMENTO', '')).strip()
                mat_atual = str(row.get('MATRICULA', '')).strip()
                cert_atual = str(row.get('CERTIFICADO', '')).strip()
                tipo_regra = row['TIPO_REGRA']
                
                # SIMULANDO O CORRESP (Pega a primeira ocorrência do nome na planilha anterior)
                match = df_conferida[df_conferida['NOME DO SEGURADO'].str.strip() == nome]
                
                cpf_relatorio = cpf_atual if tipo_regra == "EDUC" else "N/A (Modo AP)"
                
                if match.empty:
                    erros_dict[(nome, cpf_relatorio)] = ["NOME NÃO ENCONTRADO NA PLANILHA ANTERIOR"]
                    if tipo_regra == "EDUC": cont_erros_educ += 1
                    else: cont_erros_ap += 1
                    continue
                
                # Pegando os dados do corresp (primeira linha encontrada)
                row_conf = match.iloc[0]
                nome_conf = str(row_conf.get('NOME DO SEGURADO', '')).strip()
                cpf_conf = str(row_conf.get('CPF', '')).strip()
                nasc_conf = str(row_conf.get('DATA DE NASCIMENTO', '')).strip()
                mat_conf = str(row_conf.get('MATRICULA', '')).strip()
                cert_conf = str(row_conf.get('CERTIFICADO', '')).strip()
                
                inconsistencias = []
                
                # SIMULANDO O CONCATENAR (Nome + Campo Atual == Nome + Campo Anterior)
                if nome + mat_atual != nome_conf + mat_conf:
                    inconsistencias.append(f"MATRÍCULA (Atual: {mat_atual} -> Conf: {mat_conf})")
                    
                if nome + cert_atual != nome_conf + cert_conf:
                    inconsistencias.append(f"CERTIFICADO (Atual: {cert_atual} -> Conf: {cert_conf})")
                    
                if nome + nasc_atual != nome_conf + nasc_conf:
                    inconsistencias.append(f"NASCIMENTO (Atual: {nasc_atual} -> Conf: {nasc_conf})")
                    
                if tipo_regra == "EDUC":
                    if nome + cpf_atual != nome_conf + cpf_conf:
                        inconsistencias.append(f"CPF (Atual: {cpf_atual} -> Conf: {cpf_conf})")
                        
                if inconsistencias:
                    erros_dict[(nome, cpf_relatorio)] = inconsistencias
                    if tipo_regra == "EDUC": cont_erros_educ += 1
                    else: cont_erros_ap += 1

            self.atualizar_relatorio_interface(cont_erros_ap, cont_erros_educ, modo)
            self.gerar_planilha(erros_dict)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar:\n{str(e)}")
            self.lbl_relatorio.configure(text="Erro no processamento.", text_color="red")
        finally:
            self.btn_executar.configure(state="normal", text="⚡ Processar e Gerar Relatório")
            self.progress.set(1)

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
                texto_base += f"\nSistema ({esperado}) -> ✅ BATEU!"
            else:
                texto_base += f"\nSistema ({esperado}) -> ❌ DIVERGIU!"
                cor_texto = "#FF4500" # Vermelho
                
        self.lbl_relatorio.configure(text=texto_base, text_color=cor_texto)

    def gerar_planilha(self, erros_dict):
        if not erros_dict:
            messagebox.showinfo("Sucesso", "Nenhum erro encontrado! Tudo bate perfeitamente.")
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
