with 
	clean_library_tracks as (
		select
			track_id,
			artist as _artist,
			album as _album,
			name as _name,
			replace(replace(replace(replace(replace(replace(
				artist, 
				'?', '-'), '[', '-'), ']', '-'), '//', '-'), '/', '-'), '"', '-'
			) as artist,
			replace(replace(replace(replace(replace(replace(
				album, 
				'?', '-'), '[', '-'), ']', '-'), '//', '-'), '/', '-'), '"', '-'
			) as album,
			replace(replace(replace(replace(replace(replace(
				name, 
				'?', '-'), '[', '-'), ']', '-'), '//', '-'), '/', '-'), '"', '-'
			) as name,
			track_number as _track_number,
			right(CONCAT('00', cast(track_number as VARCHAR)), 2) as track_number,
			location,
			total_time,
			kind,
			source_id,
			playlist_id,
			track_database_id
		from
			library_tracks
	),
	dj_playlists as ( -- List of all DJ Playlists
		select 
			playlist_id, name, source_id
		from 
			playlists p 
		where 
			p.name not in (
				'Library', 'Downloaded',
				'Music', 'Downloaded',
				'Movies', 'Downloaded',
				'TV Shows', 'Podcasts',
				'Audiobooks', 'Purchased',
				'Unplaylisted', 'zzzzz Dumping ground pre 2025'
			)
	),
	dj_plist_tracks as ( -- All Tracks in DJ Playlists excluding AIFF, purchased, and Apple music files
		select distinct
			ptm.track_database_id,
			ptm.track_id,
			ptm.playlist_id as track_playlist_id,
			ptm.track_source_id,
			lt.artist, lt.album, 
			lt.name, lt.track_number, 
			lt.location, lt.total_time
		from 
			playlist_track_mapping ptm 
		left join 
			dj_playlists dpl
		on
			ptm.playlist_id = dpl.playlist_id
		left join
			clean_library_tracks lt 
		on
			ptm.track_database_id = lt.track_database_id
		where 
			dpl.playlist_id is not null
		and 
			/* filter out Apple music and Purchased tracks */
			lt.kind not in (
				'Purchased AAC audio file', 
				'Apple Music AAC audio file', 
				'AIFF audio file'
			)	
	),
	aifs as ( -- aif tracks in library with Bandcamp filename
		select 
			track_database_id as aif_database_id, 
			track_id as aif_track_id, 
			playlist_id as aif_playlist_id, 
			source_id as aif_source_id,
			artist as aif_artist, 
			album as aif_album, 
			name as aif_name, 
			track_number as aif_track_number, 
			location as aif_location, 
			total_time as aif_total_time,
			concat(
				artist,' - ',album,' - ',track_number,' ',name
			) as aif_bcamp_name
		from 
			clean_library_tracks lt 
		where
			kind = 'AIFF audio file'
	),
	exact_matches as ( -- 173 - Match on artist, album, and name
		select distinct
			dpt.*,
			a.*,
			'exact_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			dpt.name = a.aif_name and dpt.artist = a.aif_artist and dpt.album = a.aif_album
		where
			a.aif_database_id is not null 
	),
	exact_artist_name_matches as ( -- 10 - Match on artist and name
		select distinct
			dpt.*,
			a.*,
			'exact_artist_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			dpt.name = a.aif_name and dpt.artist = a.aif_artist
		where
			a.aif_database_id is not null
		and
			dpt.track_database_id not in (
				select track_database_id from exact_matches
			)
	),
	name_matches as ( -- 156 - exact match on name or name with track number
		select distinct
			dpt.*,
			a.*,
			'name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
				a.aif_name = dpt.name 
			or
				dpt.name = concat(a.aif_track_number, ' ', a.aif_name)
			or
				a.aif_name = concat(dpt.artist, ' - ', dpt.name)
		where
			a.aif_database_id is not null
		and
			dpt.track_database_id not in (
				select track_database_id from exact_matches
				union all
				select track_database_id from exact_artist_name_matches
			)
	),
	bcamp_matches as ( -- 153 - Match on (potentially truncated) bandcamp file name (`artist - album - song`)
		select distinct
			dpt.*,
			a.*,
			'bandcamp_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
				left(a.aif_bcamp_name, length(dpt.name)) = dpt.name
			or
				left(a.aif_bcamp_name, (length(dpt.name)-2)) = left(dpt.name, (length(dpt.name)-2))
		where
			a.aif_database_id is not null
		and
			dpt.track_database_id not in (
				select track_database_id from exact_matches
				union all
				select track_database_id from exact_artist_name_matches
				union all
				select track_database_id from name_matches
			)
	),
	total_matches as ( -- 492 - 33 unmatched - 
		select * from exact_matches -- 169
		union all
		select * from exact_artist_name_matches -- 14
		union all
		select * from name_matches -- 147
		union all
		select * from bcamp_matches -- 130
	)
select distinct
	ptm.playlist_id, 
	p.name as playlist_name, 
	p.source_id as playlist_source_id, 
	tm.*
from
	total_matches tm
left join
	playlist_track_mapping ptm
on
	ptm.track_database_id = tm.track_database_id
left join 
	dj_playlists p
on
	p.playlist_id = ptm.playlist_id
where
	tm.track_database_id is not null
and
	p.playlist_id is not null;

--select * from dj_plist_tracks;