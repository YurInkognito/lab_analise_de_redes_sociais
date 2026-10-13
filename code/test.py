from googleapiclient.discovery import build

API_KEY = "AIzaSyCrWk-Ot8uOxQl2_scAhkE3rkqOi9PAXnY"
CHANNEL_ID = "UCYj1jy66peKPzEp808TK5ww"

youtube = build("youtube", "v3", developerKey=API_KEY)

playlist_id = ("UU" + CHANNEL_ID[2:] if CHANNEL_ID.startswith("UC") else CHANNEL_ID)

print(f"--&gt; Conectado à API do YouTube.") 
print(f"--&gt; Testando busca na playlist de envios: {playlist_id}...\\n")

try:
    request = youtube.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=5)
    response = request.execute()

    items = response.get("items", [])

    if not items:
        print("nenhum video retornado para este canal")
    else:
        print(f"Sucesso Encontrados {len(items)} videos recentes neste canal:\n")
        for idx, item in enumerate(items, 1):
            snippet = item["snippet"]
            title = snippet["title"]
            published_at = snippet["publishedAt"] 
            print(f"[{idx}] {title}")
            print(f" Data de Publicação: {published_at}") 
            print("-" * 50) 

except Exception as e:
    print(f"Error ao acessar a API: {e}")