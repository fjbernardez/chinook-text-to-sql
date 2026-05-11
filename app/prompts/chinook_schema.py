CHINOOK_SCHEMA_CONTEXT = """
PostgreSQL Chinook schema, using lower_snake_case table and column names.

Allowed tables:

artist
- Primary key: artist_id
- Columns: artist_id, name
- Relationships: artist 1 to many album through album.artist_id

album
- Primary key: album_id
- Columns: album_id, title, artist_id
- Foreign keys: artist_id references artist.artist_id
- Relationships: album 1 to many track through track.album_id

track
- Primary key: track_id
- Columns: track_id, name, album_id, media_type_id, genre_id, composer, milliseconds, bytes, unit_price
- Foreign keys: album_id references album.album_id, media_type_id references media_type.media_type_id, genre_id references genre.genre_id
- Relationships: track many to many playlist through playlist_track; track 1 to many invoice_line

genre
- Primary key: genre_id
- Columns: genre_id, name
- Relationships: genre 1 to many track through track.genre_id

media_type
- Primary key: media_type_id
- Columns: media_type_id, name
- Relationships: media_type 1 to many track through track.media_type_id

playlist
- Primary key: playlist_id
- Columns: playlist_id, name
- Relationships: playlist many to many track through playlist_track

playlist_track
- Composite key: playlist_id, track_id
- Columns: playlist_id, track_id
- Foreign keys: playlist_id references playlist.playlist_id, track_id references track.track_id

customer
- Primary key: customer_id
- Columns: customer_id, first_name, last_name, company, address, city, state, country, postal_code, phone, fax, email, support_rep_id
- Foreign keys: support_rep_id references employee.employee_id
- Relationships: customer 1 to many invoice through invoice.customer_id

employee
- Primary key: employee_id
- Columns: employee_id, last_name, first_name, title, reports_to, birth_date, hire_date, address, city, state, country, postal_code, phone, fax, email
- Foreign keys: reports_to references employee.employee_id
- Relationships: employee 1 to many customer through customer.support_rep_id; employee self-reference through reports_to

invoice
- Primary key: invoice_id
- Columns: invoice_id, customer_id, invoice_date, billing_address, billing_city, billing_state, billing_country, billing_postal_code, total
- Foreign keys: customer_id references customer.customer_id
- Relationships: invoice 1 to many invoice_line through invoice_line.invoice_id

invoice_line
- Primary key: invoice_line_id
- Columns: invoice_line_id, invoice_id, track_id, unit_price, quantity
- Foreign keys: invoice_id references invoice.invoice_id, track_id references track.track_id

Business interpretation:
- Artist popularity by catalog size: artist -> album -> track
- Artist popularity by sales: artist -> album -> track -> invoice_line -> invoice
- Genre sales: genre -> track -> invoice_line -> invoice
- Customer spending: customer -> invoice, or customer -> invoice -> invoice_line
- Sales by country: invoice.billing_country or customer.country depending on the question
- Sales support representative performance: employee -> customer -> invoice
- Playlist composition: playlist -> playlist_track -> track
- Track revenue: track -> invoice_line, using invoice_line.unit_price * invoice_line.quantity
- Invoice total: invoice.total
- Track duration: track.milliseconds

Ambiguity examples:
- "best customers" is ambiguous: it could mean highest total spending, most invoices, highest average invoice value, or most tracks purchased.
- "top artists" is ambiguous: it could mean most tracks in catalog, most albums, or most revenue from sales.
- "sales by country" is ambiguous when the question does not specify invoice.billing_country or customer.country.
- "popular genre" is ambiguous: it could mean tracks sold, total revenue, or catalog size.
- "employee performance" is ambiguous: it could mean customers supported, total sales from assigned customers, or average customer spend.
""".strip()


ALLOWED_CHINOOK_TABLES = {
    "artist",
    "album",
    "track",
    "genre",
    "media_type",
    "playlist",
    "playlist_track",
    "customer",
    "invoice",
    "invoice_line",
    "employee",
}
