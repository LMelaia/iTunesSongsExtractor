from os import path

hard_coded_library_file = 'path/to/library.xml'
validation_score_needed = 3

output_file = 'path/to/out/directory'
number_of_songs_per_file = 30 # Amount of songs per csv file
number_of_songs = 0 # Change this to number of songs in library


class ITunesSongsExtractor:

    def __init__(self):
        self.outfile_number = 1
        self.outfile = open(f'{output_file}-{self.outfile_number}.csv', 'x', encoding='utf-8')
        self.library_file = ''
        self.lib_file = None

        self.line_number = 0
        self.last_line_position = 0

        self.songs_start_line_number = 0
        self.song_number = 1
        self.songs_written = 0

        self.found_xml_version = -1
        self.found_playlist_version = -1
        self.found_major_version = -1
        self.found_minor_version = -1

        self.found_n_dictionary_tags = 0

    # Get Library File

    def get_library_file(self):
        inpt = ''

        while inpt == '':
            print("Please enter valid library file path.")
            inpt = input()

        self.library_file = inpt

        if not self.check_lib_file():
            self.get_library_file()

    def check_lib_file(self):
        print('Checking library file: "' + self.library_file + '"')

        if not self.library_file.endswith('.xml'):
            print("WARN: Library doesn't end in \".xml\"")

        if not path.isfile(self.library_file):
            print("File does not exist.")
            return False
        else:
            print("Found File!")

        return True

    # Reading & Parsing

    # Prepare

    def prepare_lib_file(self):
        print(f"Attempting to read {self.library_file}...")
        file = open(self.library_file, 'r', encoding="utf8")
        print('File is accessable!')
        self.lib_file = file
        return True

    # Validate

    def is_lib_file_valid(self):
        print('Ensuring file is valid library...')
        self.read_in_versions()
        score = self.check_read_versions()

        print(f"Score: {score} / 9. Need {validation_score_needed} to pass validation.")

        if score >= validation_score_needed:
            print("Passed!")
            return True
        else:
            print("Failed!")
            return False

    def read_in_versions(self):
        self.lib_file.seek(0)

        for lineNumber in range(10):
            line = self.lib_file.readline().strip()

            if line == self.Specification.KnownTags.dictionary_open:
                self.found_n_dictionary_tags = self.found_n_dictionary_tags + 1
            elif line == self.Specification.ExpectedContent.version_xml[0]:
                self.found_xml_version = lineNumber + 1
            elif line == self.Specification.ExpectedContent.version_playlist[0]:
                self.found_playlist_version = lineNumber + 1
            elif line == self.Specification.ExpectedContent.version_major[0]:
                self.found_major_version = lineNumber + 1
            elif line == self.Specification.ExpectedContent.version_minor[0]:
                self.found_minor_version = lineNumber + 1

    @staticmethod
    def check_version(version, tag_name, expected_line):
        score = 0

        if version > 0:
            score = score + 1
            print(f"Found {tag_name} at: {version}.")
            print(f"Expected at {expected_line}")

        if version == expected_line:
            score = score + 1

        return score

    def check_read_versions(self):
        score = 0

        score = score \
          + self.check_version(
            self.found_xml_version, "XML version", self.Specification.ExpectedContent.version_xml[1]
        ) + self.check_version(
            self.found_playlist_version, "playlist version", self.Specification.ExpectedContent.version_playlist[1]
        ) + self.check_version(
            self.found_major_version, "major version", self.Specification.ExpectedContent.version_major[1]
        ) + self.check_version(
            self.found_minor_version, "minor version", self.Specification.ExpectedContent.version_minor[1]
        ) + self.found_n_dictionary_tags

        return score

    # Parse

    def find_songs_start_position(self):
        line = self.lib_file.readline().strip()
        self.line_number = self.line_number + 1

        if line == self.Specification.KnownTags.dictionary_open:
            self.found_n_dictionary_tags = self.found_n_dictionary_tags + 1

        if self.found_n_dictionary_tags != self.Specification.ExpectedContent.no_of_opening_dictionary_tags:
            self.find_songs_start_position()
        else:
            print(f"Found songs! Songs start at line {self.line_number}")
            self.songs_start_line_number = self.line_number

    def position_reader_at_songs(self):
        print("\nPositioning file reader at songs list start position...")

        self.lib_file.seek(0)
        self.line_number = 0

        for i in range(1, self.songs_start_line_number):
            self.lib_file.readline()
            self.line_number = self.line_number + 1

        print(f"File reader positioned to start reading at line {self.line_number}")
        print("File reader positioned at start of songs list!")

    def readline(self):
        self.last_line_position = self.lib_file.tell()
        line = self.lib_file.readline().strip()
        self.line_number += 1
        return line

    def seek_next_song(self):
        print('Looking for next song...')

        line = ''
        while not line == self.Specification.KnownTags.dictionary_open:
            line = self.readline()

        print('Found next song!')

    def parse_song_property(self, song, song_data_input):
        song_property = song_data_input.split(self.Specification.KnownTags.key_open)[1]
        song_property = song_property.split(self.Specification.KnownTags.key_close)[0]

        song_property_value = song_data_input.split(self.Specification.KnownTags.key_close)[1]
        song_property_value = song_property_value.replace(self.Specification.KnownTags.type_string_open, '') \
            .replace(self.Specification.KnownTags.type_string_close, '') \
            .replace(self.Specification.KnownTags.type_integer_open, '') \
            .replace(self.Specification.KnownTags.type_integer_close, '') \
            .replace(self.Specification.KnownTags.type_date_open, '') \
            .replace(self.Specification.KnownTags.type_date_close, '')

        self.try_write_to_song(song, song_property, song_property_value)

    def try_write_to_song(self, song, song_property, song_property_value):
        if self.line_number != 0:
            for song_property_holder in song.all_properties:
                if song_property_holder.get() == song_property:
                    print(f'  Saving "{song_property_value}" under key "{song_property}"', end='  |')
                    song_property_holder.set(song_property_value)

    def read_song(self):
        print(f'\nReading song ({self.song_number}) at line {self.line_number}')
        song = self.Song()

        while True:
            song_property = self.readline()
            if song_property == self.Specification.KnownTags.dictionary_close:
                break
            else:
                self.parse_song_property(song, song_property)

        self.song_number += 1

        print(f'\nFinished reading song({self.song_number - 1}) -> name="{song.name}"')
        print(f'Ends at line {self.line_number}')
        return song

    def read_songs(self):
        print("\nReady! Reading songs...")

        self.write_song_to_output(self.Song())

        for i in range(number_of_songs):
            self.seek_next_song()
            song = self.read_song()
            self.write_song_to_output(song)

    # Write to output file

    def open_new_outfile(self):
        self.outfile.flush()
        self.outfile.close()

        self.outfile_number += 1
        self.songs_written = 0
        self.outfile = open(f'{output_file}-{self.outfile_number}.csv', 'x', encoding='utf-8')
        self.write_song_to_output(self.Song())

    def write_song_to_output(self, song):
        if self.songs_written >= number_of_songs_per_file:
            self.open_new_outfile()

        line_to_write = ''
        for songValue in song.all_properties:
            line_to_write += f'"{songValue}",'

        self.outfile.write(line_to_write + '\n')
        self.songs_written += 1

    # Sequences

    def begin_parse_sequence(self):
        print("Preparing to parse songs...")

        # Parse setup
        self.find_songs_start_position()
        self.position_reader_at_songs()
        self.read_songs()

    def begin_read_sequence(self):
        print(f"\nAccepted '{self.library_file}'!\nPreparing to read library...")

        # Prepare
        is_prepared = self.prepare_lib_file() and self.lib_file is not None
        if not is_prepared:
            print("\nFAILURE! Could not prepare file for reading.")
            exit(1)
        else:
            print('\nFile prepared for reading!')

        # Validate
        is_valid = self.is_lib_file_valid()
        if not is_valid:
            print("\nFAILURE! Library file is invalid.")
        else:
            print('\nFile validiated!')
            self.line_number = 10

        # Parse
        self.begin_parse_sequence()

    # Main / simple begin

    def begin(self, const_library_file):
        print("Beginning...")

        if const_library_file == '':
            print("No hard scripted library file!")
            self.get_library_file()
        else:
            self.library_file = const_library_file

        if not self.check_lib_file():
            self.get_library_file()

        self.begin_read_sequence()

    class Song:

        class MutableSongValue:
            def __init__(self, value):
                self.value = value

            def __str__(self):
                return self.value

            def set(self, value):
                self.value = value

            def get(self):
                return self.value

        def __init__(self):
            self.name = self.MutableSongValue('Name')
            self.name_sort = self.MutableSongValue('Sort Name')
            self.artist = self.MutableSongValue('Artist')
            self.artist_sort = self.MutableSongValue('Sort Artist')
            self.album = self.MutableSongValue('Album')
            self.album_sort = self.MutableSongValue('Sort Album')
            self.play_count = self.MutableSongValue('Play Count')
            self.skip_count = self.MutableSongValue('Skip Count')
            self.composer = self.MutableSongValue('Composer')
            self.genre = self.MutableSongValue('Genre')
            self.year = self.MutableSongValue('Year')
            self.track_number = self.MutableSongValue('Track Number')
            self.track_count = self.MutableSongValue('Track Count')
            self.disc_number = self.MutableSongValue('Disc Number')
            self.disc_count = self.MutableSongValue('Disc Count')
            self.loved = self.MutableSongValue('Loved')
            self.compilation = self.MutableSongValue('Compilation')
            self.subscription = self.MutableSongValue('Apple Music')
            self.date_added = self.MutableSongValue('Date Added')
            self.date_released = self.MutableSongValue('Release Date')
            self.all_properties = [
                self.name, self.name_sort, self.artist, self.artist_sort, self.album, self.album_sort, self.play_count,
                self.skip_count, self.composer, self.genre, self.year, self.track_number, self.track_count,
                self.disc_number, self.disc_count, self.loved, self.compilation, self.subscription, self.date_added,
                self.date_released
            ]

    # A whole bunch of both known and expected data about the library
    # Used to parse it
    class Specification:

        # List of XML tags known to be used to structure the library
        # Used to parse the library
        class KnownTags:
            dictionary_open = '<dict>'
            dictionary_close = '</dict>'
            key_open = '<key>'
            key_close = '</key>'

            type_string_open = '<string>'
            type_string_close = '</string>'
            type_integer_open = '<integer>'
            type_integer_close = '</integer>'
            type_date_open = '<date>'
            type_date_close = '</date>'

        # Content known to be in an iTunes library
        # Used to check if given file is a valid library
        # All expected text content is stored in an array with the line
        # number the content is expected on.
        class ExpectedContent:
            version_xml = ['<?xml version="1.0" encoding="UTF-8"?>', 1]
            version_playlist = ['<plist version="1.0">', 3]
            version_major = ['<key>Major Version</key><integer>1</integer>', 5]
            version_minor = ['<key>Minor Version</key><integer>1</integer>', 6]

            no_of_opening_dictionary_tags = 3


if __name__ == '__main__':
    ITunesSongsExtractor().begin(hard_coded_library_file)
