export interface FavoriteItem {
  id: string;
  item_type: 'event' | 'model' | 'chart';
  title: string;
  saved_at: string;
  path: string;
}

export interface FavoritesResponse {
  favorites: FavoriteItem[];
}
