/*

NOTE (Mike):
I created this table manually on our edw instance to slowly migrate to the new system 
without breaking the old.

*/
CREATE TABLE indicator_data_visual_source (
  id SERIAL PRIMARY KEY,
  data_visual_id INTEGER NOT NULL,
  source_id INTEGER NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,

  CONSTRAINT indicator_data_visual_source_data_visual_id_fkey
      FOREIGN KEY (data_visual_id)
      REFERENCES indicator_data_visual(id)
      ON DELETE CASCADE
      DEFERRABLE INITIALLY DEFERRED,

  CONSTRAINT indicator_data_visual_source_source_id_fkey
      FOREIGN KEY (source_id)
      REFERENCES indicator_source(id)
      ON DELETE CASCADE
      DEFERRABLE INITIALLY DEFERRED,

  CONSTRAINT indicator_data_visual_source_data_visual_id_source_id_uniq
      UNIQUE (data_visual_id, source_id)
);

CREATE INDEX indicator_data_visual_source_data_visual_id_idx
  ON indicator_data_visual_source(data_visual_id);

CREATE INDEX indicator_data_visual_source_source_id_idx
  ON indicator_data_visual_source(source_id);

CREATE INDEX indicator_data_visual_source_priority_idx
  ON indicator_data_visual_source(priority);
