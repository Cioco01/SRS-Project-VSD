-- Tabella per gli eventi di traffico di rete RAW catturati da tcpdump
CREATE TABLE IF NOT EXISTS raw_network_traffic (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp_capture BIGINT NOT NULL,   -- Timestamp Unix del momento della cattura
    source_ip VARCHAR(45) NOT NULL,
    destination_ip VARCHAR(45) NOT NULL,
    source_port INT,
    destination_port INT,
    protocol VARCHAR(10) NOT NULL,
    packet_length INT,                   -- Lunghezza del pacchetto
    flags VARCHAR(20),                   -- Flag TCP (es. SYN, ACK, FIN)
    ttl INT,                             -- Time To Live
    description TEXT,                    -- Descrizione parsata o log aggiuntivo
    full_line TEXT NOT NULL,             -- La riga completa di tcpdump
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
