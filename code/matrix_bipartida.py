import json
import itertools
import pandas as pd

INPUT_FILENAME = "DADOS_COMENTARIOS.json"
BIPARTITE_OUTPUT = "matriz_bipartida.csv"
OVERLAP_OUTPUT = "rede_sobreposicao.csv"

def load_data(filename):
    print(f"Lendo o arquivo {filename}...")
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_audience_sets(data):
    
    channel_users = {}
    
    for channel in data.get("channels", []):
        c_id = channel["channel_id"]
        users = set()
        
        for video in channel.get("videos", []):
            for comment in video.get("comments", []):
                author_id = comment.get("author_id")
                if author_id and author_id != "ANONYMOUS":
                    users.add(author_id)
                    
        channel_users[c_id] = users
        print(f" Canal {c_id}: {len(users)} usuários únicos identificados.")
        
    return channel_users

def export_bipartite_network(channel_users, output_filename):
    
    print("\nGerando matriz bipartida (Edge List)...")
    edges = []
    
    for channel_id, users in channel_users.items():
        for user_id in users:
            edges.append({"Source": user_id, "Target": channel_id, "Type": "Undirected"})
            
    df_bipartite = pd.DataFrame(edges)
    df_bipartite.to_csv(output_filename, index=False)
    print(f" -> Salvo em {output_filename} ({len(edges)} conexões)")

def calculate_jaccard_overlap(channel_users, output_filename):
   
    print("\nCalculando Coeficiente de Jaccard e sobreposição...")
    channels = list(channel_users.keys())
    
    overlap_edges = []
    
    matrix_data = {c: {c_inner: 0.0 for c_inner in channels} for c in channels}
    
    for c1, c2 in itertools.combinations(channels, 2):
        set1 = channel_users[c1]
        set2 = channel_users[c2]
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        jaccard = (intersection / union) if union > 0 else 0.0
        
        if jaccard > 0:
            overlap_edges.append({
                "Source": c1,
                "Target": c2,
                "Type": "Undirected",
                "Weight_Jaccard": round(jaccard, 4),
                "Common_Users": intersection
            })
            
        matrix_data[c1][c2] = jaccard
        matrix_data[c2][c1] = jaccard

    for c in channels:
        matrix_data[c][c] = 1.0

    df_overlap = pd.DataFrame(overlap_edges)
    df_overlap.to_csv(output_filename, index=False)
    print(f" -> Arestas da rede salvas em {output_filename}")
    
    return matrix_data

def main():
    try:
        data = load_data(INPUT_FILENAME)
    except FileNotFoundError:
        print(f"[Erro] O arquivo {INPUT_FILENAME} não foi encontrado no diretório atual.")
        return

    channel_users = build_audience_sets(data)
    
    export_bipartite_network(channel_users, BIPARTITE_OUTPUT)
    
    matrix_data = calculate_jaccard_overlap(channel_users, OVERLAP_OUTPUT)
    
    df_matrix = pd.DataFrame(matrix_data)
    print("\n" + "="*50)
    print(" MATRIZ DE SIMILARIDADE DE JACCARD (Canal x Canal):")
    print("="*50)
    pd.set_option('display.max_columns', None) 
    pd.set_option('display.width', 1000)
    print(df_matrix.round(4))
    print("="*50)

if __name__ == "__main__":
    main()