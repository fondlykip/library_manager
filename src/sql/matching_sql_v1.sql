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
			itunes.library_tracks
	),
	dj_playlists as ( -- List of all DJ Playlists
		select 
			playlist_id
		from 
			itunes.playlists p 
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
			itunes.playlist_track_mapping ptm 
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
				artist, ' - ', album, ' - ', 
				right(concat('00', cast(track_number as VARCHAR)), 2), 
				' ', name
			) as bcamp_name
		from 
			clean_library_tracks lt 
		where
			kind = 'AIFF audio file'
	),
	exact_matches as ( -- 169 - Match on artist, album, and name
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
	exact_artist_name_matches as ( -- 14 - Match on artist and name
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
	exact_album_name_matches as ( -- 0 - Match on Album and Name
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'exact_album_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			dpt.name = a.name and dpt.album = a.album
		where
			a.track_id is not null
		and
			dpt.track_id not in (
				select track_id from exact_matches
				union all
				select track_id from exact_artist_name_matches
			)
	),
	name_matches as ( -- 151 - exact match on name or name with track number
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
			dpt.name = concat(
							a.track_number, 
							' ', 
							a.name
						)
		or 
			dpt.name = a.name
		where
			a.track_id is not null
		and
			dpt.track_id not in (
				select track_id from exact_matches
				union all
				select track_id from exact_artist_name_matches
			)
	),
	bcamp_matches as ( -- 130 - Match on (potentially truncated) bandcamp file name (`artist - album - song`)
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
				(left(a.bcamp_name, length(dpt.name)) = dpt.name)
			or
				(left(a.bcamp_name, length(dpt.name)-2) = dpt.name)
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
	), /*
	exact_and_fuzzy_name_matches as ( -- 7 (one duplicate) - Match on artist, album, and fuzzy name
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'exact_artist_album_fuzzy_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			a.artist = dpt.artist and a.album = dpt.album and (
					a.name like '%' || dpt.name || '%'
				or
					dpt.name like '%' || a.name || '%'
				or
					a.name like dpt.name || '%'
				or
					a.name like '%' || dpt.name
				or
					dpt.name like a.name || '%'
				or
					dpt.name like '%' || a.name
			)
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
	exact_artist_and_fuzzy_name_matches as ( -- 2 (one duplicate) - Match on artist, album, and fuzzy name
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'exact_artist_fuzzy_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
			a.artist = dpt.artist and (
					a.name like '%' || dpt.name || '%'
				or
					dpt.name like '%' || a.name || '%'
				or
					a.name like dpt.name || '%'
				or
					a.name like '%' || dpt.name
				or
					dpt.name like a.name || '%'
				or
					dpt.name like '%' || a.name
			)
		where
			a.track_id is not null
		and
			dpt.track_id not in (
				select track_id from exact_matches
				union all
				select track_id from exact_artist_name_matches
				union all
				select track_id from name_matches
				union all
				select track_id from exact_and_fuzzy_name_matches
			)
	), 
	fuzzy_name_matches as ( -- Match on fuzzy name only
		select distinct
			dpt.*,
			a.track_id as aif_id,
			a.bcamp_name,
			a.location as aif_location,
			a.artist as aif_artist,
			a.album as aif_album,
			a.name as aif_name,
			a.total_time as aif_time,
			'fuzzy_name_match' as match_type
		from
			dj_plist_tracks dpt
		left join
			aifs a
		on
				(
						a.name like '%' || dpt.name || '%'
					or
						dpt.name like '%' || a.name || '%'
				)
				or
				(
						a.name like dpt.name || '%'
					or
						a.name like '%' || dpt.name
				)
				or
				(
						dpt.name like a.name || '%'
					or
						dpt.name like '%' || a.name
				)
		where
			a.track_id is not null
		and
			dpt.track_id not in (
				select track_id from exact_matches
				union all
				select track_id from exact_artist_name_matches
				union all
				select track_id from name_matches
				union all
				select track_id from exact_and_fuzzy_name_matches
				union all 
				select track_id from exact_artist_and_fuzzy_name_matches
				union all
				select track_id from bcamp_matches
			)
	), */
	total_matches as ( -- only 41 unmatched - 
		select * from exact_matches -- 169
		union all
		select * from exact_artist_name_matches -- 14
		union all
		select * from exact_album_name_matches -- 0
		union all
		select * from name_matches -- 147
		union all
		select * from bcamp_matches -- 130
		-- union all
		-- select * from exact_and_fuzzy_name_matches -- 7
		-- union all 
		-- select * from exact_artist_and_fuzzy_name_matches -- 2
	)
/*
select distinct
	track_id, aif_id, *
from
	total_matches;
*/
select
	*
from
	exact_album_name_matches;
	--aifs dpt
	--album_artist_matches dpt
	dj_plist_tracks dpt
where 
	dpt.track_id not in (
		select track_id from total_matches
	);
