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
			kind
		from
			library_tracks
	),
	dj_playlists as ( -- List of all DJ Playlists
		select 
			playlist_id
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
			ptm.track_id,
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
			ptm.track_id = lt.track_id
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
			track_id, artist, 
			album, name, 
			track_number, location, 
			total_time,
			concat(
				artist,' - ',album,' - ',track_number,' ',name
			) as bcamp_name
		from 
			clean_library_tracks lt 
		where
			kind = 'AIFF audio file'
	),
	exact_matches as ( -- 173 - Match on artist, album, and name
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'exact_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			dpt.name = a.name and dpt.artist = a.artist and dpt.album = a.album
		where
			a.track_id is not null 
	),
	exact_artist_name_matches as ( -- 10 - Match on artist and name
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'exact_artist_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			dpt.name = a.name and dpt.artist = a.artist
		where
			a.track_id is not null
		and
			dpt.track_id not in (
				select track_id from exact_matches
			)
	),
	name_matches as ( -- 156 - exact match on name or name with track number
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			a.name = dpt.name 
		or
			dpt.name = concat(a.track_number, ' ', a.name)
		or
			a.name = concat(dpt.artist, ' - ', dpt.name)
		where
			a.track_id is not null
		and
			dpt.track_id not in (
				select track_id from exact_matches
				union all
				select track_id from exact_artist_name_matches
			)
	),
	bcamp_matches as ( -- 153 - Match on (potentially truncated) bandcamp file name (`artist - album - song`)
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'bandcamp_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
				left(a.bcamp_name, length(dpt.name)) = dpt.name
			or
				left(a.bcamp_name, (length(dpt.name)-2)) = left(dpt.name, (length(dpt.name)-2))
		where
			a.track_id is not null
		and
			dpt.track_id not in (
				select track_id from exact_matches
				union all
				select track_id from exact_artist_name_matches
				union all
				select track_id from name_matches
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
	ptm.playlist_id, tm.track_id, tm.aif_id
from
	total_matches tm
left join
	playlist_track_mapping ptm
on
	ptm.track_id = tm.track_id
where
	tm.track_id is not null;

--select * from dj_plist_tracks;