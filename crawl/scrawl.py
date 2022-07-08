from generate_info import get_info
from search_for_list import get_playlist

genre = "摇滚"
ids = get_playlist(genre)
music_info = get_info(ids)
print(music_info)
# print(x)
# print(y)


