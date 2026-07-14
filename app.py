import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
from fpdf import FPDF
import threading
import os

# Configuração visual moderna
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ComparadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Comparador de Segurados")
        self.geometry("650x500")
        self.resizable(False, False)
        
        self.arquivo_atual = ""
        self.arquivo_conferido = ""
        
        # Interface - Título
        self.lbl_title = ctk.CTkLabel(self, text="Verificador de Inconsistências", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=(20, 10))
        
        # Interface - Seleção de Arquivos
        self.btn_atual = ctk.CTkButton(self, text="1. Escolher Planilha Atual", command=self.selecionar_atual, width=300)
        self.btn_atual.pack(pady=10)
        self.lbl_atual = ctk.CTkLabel(self, text="Nenhum arquivo atual selecionado", text_color="gray")
        self.lbl_atual.pack()
        
        self.btn_conferido = ctk.CTkButton(self, text="2. Escolher Planilha a Conferir", command=self.selecionar_conferida, width=300)
        self.btn_conferido.pack(pady=(20, 10))
        self.lbl_conferido = ctk.CTkLabel(self, text="Nenhum arquivo para conferência selecionado", text_color="gray")
        self.lbl_conferido.pack()
        
        # Interface - Barra de Progresso
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=25)
        self.progress.set(0)
        
        # Interface - Botão de Execução
        self.btn_executar = ctk.CTkButton(self, text="Verificar e Gerar PDF", command=self.iniciar_thread_verificacao, 
                                          fg_color="#28a745", hover_color="#218838", font=("Roboto", 16, "bold"), width=300, height=40)
        self.btn_executar.pack(pady=10)
        
        # Interface - Rodapé
        self.lbl_footer = ctk.CTkLabel(self, text="Criado por Matheus Carvalho", font=("Roboto", 12, "italic"), text_color="gray")
        self.lbl_footer.pack(side="bottom", pady=15)

    def selecionar_atual(self):
        self.arquivo_atual = filedialog.askopenfilename(filetypes=[("Arquivos de Texto e CSV", "*.txt *.csv *.TXT")])
        if self.arquivo_atual:
            self.lbl_atual.configure(text=os.path.basename(self.arquivo_atual), text_color="white")

    def selecionar_conferida(self):
        self.arquivo_conferido = filedialog.askopenfilename(filetypes=[("Arquivos de Texto e CSV", "*.txt *.csv *.TXT")])
        if self.arquivo_conferido:
            self.lbl_conferido.configure(text=os.path.basename(self.arquivo_conferido), text_color="white")

    def ler_arquivo(self, caminho):
        try:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='utf-8-sig').fillna("")
        except UnicodeDecodeError:
            return pd.read_csv(caminho, sep=';', dtype=str, encoding='latin-1').fillna("")

    def iniciar_thread_verificacao(self):
        if not self.arquivo_atual or not self.arquivo_conferido:
            messagebox.showwarning("Aviso", "Por favor, selecione os dois arquivos antes de continuar.")
            return
        
        self.btn_executar.configure(state="disabled", text="Processando...")
        self.progress.set(0)
        threading.Thread(target=self.processar_planilhas).start()

    def processar_planilhas(self):
        try:
            df_atual = self.ler_arquivo(self.arquivo_atual)
            df_conferida = self.ler_arquivo(self.arquivo_conferido)
            
            erros = []
            total_linhas = len(df_atual)
            
            for idx, row in df_atual.iterrows():
                self.progress.set((idx + 1) / total_linhas)
                self.update_idletasks()
                
                nome = str(row.get('NOME DO SEGURADO', '')).strip()
                cpf = str(row.get('CPF', '')).strip()
                nasc = str(row.get('DATA DE NASCIMENTO', '')).strip()
                matricula = str(row.get('MATRICULA', '')).strip()
                certificado = str(row.get('CERTIFICADO', '')).strip()
                
                if not nome and not cpf:
                    continue
                
                match = df_conferida[(df_conferida['NOME DO SEGURADO'].str.strip() == nome) & 
                                     (df_conferida['CPF'].str.strip() == cpf)]
                
                if match.empty:
                    erros.append(f"NOME/CPF NAO ENCONTRADO OU DIVERGENTE: {nome} (CPF: {cpf})")
                else:
                    row_conf = match.iloc[0]
                    
                    if nasc != str(row_conf.get('DATA DE NASCIMENTO', '')).strip():
                        erros.append(f"DIVERGENCIA - DATA NASCIMENTO | {nome} | Atual: {nasc} | Conferida: {row_conf.get('DATA DE NASCIMENTO')}")
                    
                    if matricula != str(row_conf.get('MATRICULA', '')).strip():
                        erros.append(f"DIVERGENCIA - MATRICULA | {nome} | Atual: {matricula} | Conferida: {row_conf.get('MATRICULA')}")
                        
                    if certificado != str(row_conf.get('CERTIFICADO', '')).strip():
                        erros.append(f"DIVERGENCIA - CERTIFICADO | {nome} | Atual: {certificado} | Conferida: {row_conf.get('CERTIFICADO')}")

            self.gerar_pdf(erros)
            
        except Exception as e:
            messagebox.showerror("Erro de Processamento", f"Ocorreu um erro ao ler os arquivos:\n{str(e)}")
        finally:
            self.btn_executar.configure(state="normal", text="Verificar e Gerar PDF")
            self.progress.set(1)

    def gerar_pdf(self, erros):
        if not erros:
            messagebox.showinfo("Sucesso", "Nenhum erro ou divergência encontrado! Os arquivos batem perfeitamente.")
            return

        pdf_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialfile="Relatorio_Inconsistencias.pdf")
        if not pdf_path:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Relatorio de Inconsistencias - Segurados", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Total de inconsistencias encontradas: {len(erros)}", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=9)
        for erro in erros:
            pdf.multi_cell(0, 8, txt=erro.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(2)
            
        try:
            pdf.output(pdf_path)
            messagebox.showinfo("Sucesso", f"Relatorio salvo com sucesso em:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar PDF", f"Não foi possível salvar o PDF.\n{str(e)}")

if __name__ == "__main__":
    app = ComparadorApp()
    app.mainloop()
