import json
import pandas as pd

INPUT_FILENAME = "DADOS_COMENTARIOS.json"
REPORT_FILENAME = "relatorio_extracao.csv"

def main():
    try:
        print(f"Lendo o arquivo {INPUT_FILENAME}...")
        with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[Erro] O arquivo '{INPUT_FILENAME}' não foi encontrado.")
        return

    relatorio = []

    for channel in data.get("channels", []):
        channel_id = channel.get("channel_id", "Desconhecido")
        
        total_videos_encontrados = channel.get("total_videos", 0)
        
        videos_list = channel.get("videos", [])
        videos_processados_total = len(videos_list)
        
        videos_com_comentarios = 0
        total_comentarios_canal = 0
        
        for video in videos_list:
            qtd_comentarios = video.get("comments_count", 0)
            total_comentarios_canal += qtd_comentarios
            
            if qtd_comentarios > 0:
                videos_com_comentarios += 1

        status = "OK"
        if total_videos_encontrados > 0:
            if total_comentarios_canal == 0:
                status = "ALERTA: Zero comentários (Cota estourou antes de começar ou canal bloqueia comentários)"
            elif videos_com_comentarios < total_videos_encontrados:
                status = "AVISO: Extração parcial (Alguns vídeos ficaram com 0 comentários. Pode ser o limite da cota)"

        relatorio.append({
            "ID_do_Canal": channel_id,
            "Videos_no_Periodo": total_videos_encontrados,
            "Videos_com_Comentarios_Salvos": videos_com_comentarios,
            "Total_Comentarios_Extraidos": total_comentarios_canal,
            "Status_da_Extracao": status
        })

    df = pd.DataFrame(relatorio)
    
    df.to_csv(REPORT_FILENAME, index=False, sep=";", encoding="utf-8-sig")
    
    print("\n" + "="*80)
    print(" RESUMO DA EXTRAÇÃO POR CANAL:")
    print("="*80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df.drop(columns=["Status_da_Extracao"]).to_string(index=False)) 
    print("="*80)
    print(f"\nRelatório completo salvo em: {REPORT_FILENAME} (Abra no Excel para ver a coluna de Status)")

if __name__ == "__main__":
    main()