export interface Settings {
    api_key: string
    app_data_dir: string
    exclude_words: string
    version: string
    server_start_time: string
    timezone: string
    log_level: string
    monitor_enabled: boolean
    monitor_interval: number
    trailer_file_name: string
    trailer_folder_movie: boolean
    trailer_folder_series: boolean
    trailer_always_search: boolean
    trailer_search_query: string
    trailer_resolution: number
    trailer_audio_format: string
    trailer_audio_volume_level: number
    trailer_video_format: string
    trailer_subtitles_enabled: boolean
    trailer_subtitles_format: string
    trailer_subtitles_language: string
    trailer_check_plex: boolean
    trailer_file_format: string
    trailer_embed_metadata: boolean
    trailer_remove_sponsorblocks: boolean
    trailer_web_optimized: boolean
    trailer_min_duration: number
    trailer_max_duration: number
    update_available: boolean
    wait_for_media: boolean
    yt_cookies_path: string
    trailer_remove_silence: boolean
}

export interface ServerStats {
    trailers_downloaded: number
    movies_count: number
    movies_monitored: number
    series_count: number
    series_monitored: number
}