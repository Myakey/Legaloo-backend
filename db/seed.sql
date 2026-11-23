-- Legaloo seed data. Run AFTER schema.sql in the Supabase SQL editor.
--
-- Part 1 (curriculum) is safe to re-run: courses/levels are upserted, lesson steps are rebuilt.
-- Part 2 (demo users) DELETES and recreates the two demo accounts with progress dated relative
-- to "today" in Asia/Jakarta. Re-run the whole file on the morning of the demo so the streak
-- and the daily bar look right (otherwise yesterday's "today" becomes a broken streak).
--
-- Illustrations: lessons do not store images. A step can carry an "illustration" key
-- (e.g. CROSSING_GREEN) that the Android app maps to its own Compose Canvas drawing.

begin;

-- ======================================================== Part 1: curriculum

insert into courses (id, number, title, unit_number, unit_label) values (1, 1, 'Hak dan Kewajiban', 2, 'KURSUS 1, UNIT 2')
  on conflict (id) do update set number = excluded.number, title = excluded.title, unit_number = excluded.unit_number, unit_label = excluded.unit_label;
insert into courses (id, number, title, unit_number, unit_label) values (2, 2, 'Aturan di Sekolah', 1, 'KURSUS 2, UNIT 1')
  on conflict (id) do update set number = excluded.number, title = excluded.title, unit_number = excluded.unit_number, unit_label = excluded.unit_label;
insert into courses (id, number, title, unit_number, unit_label) values (3, 3, 'Keluarga dan Hukum', 1, 'KURSUS 3, UNIT 1')
  on conflict (id) do update set number = excluded.number, title = excluded.title, unit_number = excluded.unit_number, unit_label = excluded.unit_label;
insert into courses (id, number, title, unit_number, unit_label) values (4, 4, 'Aturan Lalu Lintas', 1, 'KURSUS 4, UNIT 1')
  on conflict (id) do update set number = excluded.number, title = excluded.title, unit_number = excluded.unit_number, unit_label = excluded.unit_label;

delete from levels where course_id not in (1, 2, 3, 4);
delete from levels where course_id = 1 and position > 5;
delete from levels where course_id = 2 and position > 5;
delete from levels where course_id = 3 and position > 5;
delete from levels where course_id = 4 and position > 4;

insert into levels (course_id, position, type, title) values
  (1, 1, 'LESSON', 'Apa Itu Hak?'),
  (1, 2, 'LESSON', 'Apa Itu Kewajiban?'),
  (1, 3, 'LESSON', 'Hak dan Kewajiban Harus Seimbang'),
  (1, 4, 'LESSON', 'Hak Anak Dilindungi Hukum'),
  (1, 5, 'PRACTICE', 'Latihan: Hak dan Kewajiban'),
  (2, 1, 'LESSON', 'Kenapa Sekolah Punya Aturan?'),
  (2, 2, 'LESSON', 'Wajib Belajar'),
  (2, 3, 'LESSON', 'Stop Perundungan'),
  (2, 4, 'LESSON', 'Menjaga Fasilitas Sekolah'),
  (2, 5, 'PRACTICE', 'Latihan: Aturan di Sekolah'),
  (3, 1, 'LESSON', 'Keluarga Itu Apa?'),
  (3, 2, 'LESSON', 'Akta Kelahiran'),
  (3, 3, 'LESSON', 'Tugas Orang Tua'),
  (3, 4, 'LESSON', 'Batas Usia Menikah'),
  (3, 5, 'PRACTICE', 'Latihan: Keluarga dan Hukum'),
  (4, 1, 'LESSON', 'Rambu dan Lampu Lalu Lintas'),
  (4, 2, 'LESSON', 'Pakai Helm!'),
  (4, 3, 'LESSON', 'SIM dan Batas Usia'),
  (4, 4, 'PRACTICE', 'Latihan: Aturan Lalu Lintas')
  on conflict (course_id, position) do update set type = excluded.type, title = excluded.title;

delete from lesson_steps;
insert into lesson_steps (course_id, level_position, position, kind, mode_label, title, content, mascot_message) values
  (1, 1, 1, 'READ', 'MODE BACA', 'Apa Itu Hak?', '{"paragraphs": ["Hak adalah sesuatu yang boleh kamu dapatkan atau lakukan. Hak dimiliki setiap orang, termasuk anak-anak.", "Contoh hak anak: bermain, belajar di sekolah, mendapat makanan yang sehat, dan dilindungi dari kekerasan."]}'::jsonb, 'Ayo kita mulai!'),
  (1, 1, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Manakah yang merupakan contoh hak anak?", "options": [{"text": "Mendapat pendidikan", "correct": true}, {"text": "Membayar pajak", "correct": false}, {"text": "Mengendarai mobil sendiri", "correct": false}, {"text": "Bekerja di pabrik", "correct": false}], "feedbackCorrect": "Benar! Setiap anak berhak mendapat pendidikan.", "feedbackWrong": "Kurang tepat. Jawaban yang benar: mendapat pendidikan."}'::jsonb, 'Pilih jawabanmu!'),
  (1, 2, 1, 'READ', 'MODE BACA', 'Apa Itu Kewajiban?', '{"paragraphs": ["Kewajiban adalah sesuatu yang harus kamu lakukan. Kewajiban membuat hidup bersama jadi tertib.", "Contoh kewajiban anak: belajar dengan sungguh-sungguh, menghormati orang tua dan guru, serta menjaga kebersihan."]}'::jsonb, 'Kewajiban itu tanggung jawab kita!'),
  (1, 2, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Manakah contoh kewajiban seorang siswa?", "options": [{"text": "Bermain gim sepanjang hari", "correct": false}, {"text": "Mengerjakan tugas dari guru", "correct": true}, {"text": "Pulang sebelum bel berbunyi", "correct": false}, {"text": "Mencoret meja kelas", "correct": false}], "feedbackCorrect": "Hebat! Mengerjakan tugas adalah kewajiban siswa.", "feedbackWrong": "Kurang tepat. Jawaban yang benar: mengerjakan tugas dari guru."}'::jsonb, 'Pilih jawabanmu!'),
  (1, 3, 1, 'READ', 'MODE BACA', 'Hak dan Kewajiban Harus Seimbang', '{"paragraphs": ["Kita boleh menuntut hak, tetapi kita juga harus menjalankan kewajiban. Keduanya harus seimbang.", "Hak kita juga dibatasi oleh hak orang lain. Misalnya, kamu berhak bermain musik, tetapi jangan sampai mengganggu tetangga yang sedang beristirahat."]}'::jsonb, 'Seimbang itu penting!'),
  (1, 3, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Doni ingin bermain bola, tetapi PR-nya belum selesai. Apa yang sebaiknya Doni lakukan?", "options": [{"text": "Bermain dulu, PR besok saja", "correct": false}, {"text": "Menyuruh temannya mengerjakan PR", "correct": false}, {"text": "Menyelesaikan PR dulu, lalu bermain", "correct": true}, {"text": "Tidak mengerjakan PR sama sekali", "correct": false}], "feedbackCorrect": "Benar! Jalankan kewajiban dulu, lalu nikmati hakmu.", "feedbackWrong": "Kurang tepat. Sebaiknya Doni menyelesaikan PR dulu, lalu bermain."}'::jsonb, 'Pilih jawabanmu!'),
  (1, 4, 1, 'READ', 'MODE BACA', 'Hak Anak Dilindungi Hukum', '{"paragraphs": ["Di Indonesia, hak anak dilindungi oleh Undang-Undang Perlindungan Anak (UU No. 23 Tahun 2002 yang diubah dengan UU No. 35 Tahun 2014).", "Menurut undang-undang itu, anak adalah seseorang yang belum berusia 18 tahun, termasuk yang masih dalam kandungan.", "Jika ada yang menyakitimu, ceritakan kepada orang tua, guru, atau orang dewasa yang kamu percaya."]}'::jsonb, 'Kamu tidak sendirian!'),
  (1, 4, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Menurut UU Perlindungan Anak, siapa yang disebut anak?", "options": [{"text": "Seseorang yang belum berusia 12 tahun", "correct": false}, {"text": "Seseorang yang belum berusia 18 tahun", "correct": true}, {"text": "Seseorang yang masih SD", "correct": false}, {"text": "Seseorang yang belum menikah", "correct": false}], "feedbackCorrect": "Benar! Anak adalah seseorang yang belum berusia 18 tahun.", "feedbackWrong": "Kurang tepat. Anak adalah seseorang yang belum berusia 18 tahun."}'::jsonb, 'Pilih jawabanmu!'),
  (1, 5, 1, 'QUIZ', 'MODE KUIS', null, '{"question": "Mendapat makanan yang sehat termasuk...", "options": [{"text": "Hak", "correct": true}, {"text": "Kewajiban", "correct": false}, {"text": "Larangan", "correct": false}, {"text": "Hukuman", "correct": false}], "feedbackCorrect": "Benar! Itu adalah hak anak.", "feedbackWrong": "Kurang tepat. Itu adalah hak anak."}'::jsonb, 'Latihan dimulai!'),
  (1, 5, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Menjaga kebersihan kelas termasuk...", "options": [{"text": "Hak", "correct": false}, {"text": "Kewajiban", "correct": true}, {"text": "Hadiah", "correct": false}, {"text": "Pilihan saja", "correct": false}], "feedbackCorrect": "Benar! Itu kewajiban kita bersama.", "feedbackWrong": "Kurang tepat. Itu adalah kewajiban."}'::jsonb, 'Pilih jawabanmu!'),
  (1, 5, 3, 'QUIZ', 'MODE KUIS', null, '{"question": "Rina berhak bermain, tetapi temannya sedang belajar di dekatnya. Apa yang tepat?", "options": [{"text": "Bermain sambil berteriak", "correct": false}, {"text": "Bermain di tempat lain agar tidak mengganggu", "correct": true}, {"text": "Mengambil buku temannya", "correct": false}, {"text": "Menyalakan musik keras-keras", "correct": false}], "feedbackCorrect": "Benar! Hak kita dibatasi oleh hak orang lain.", "feedbackWrong": "Kurang tepat. Sebaiknya Rina bermain di tempat lain."}'::jsonb, 'Pilih jawabanmu!'),
  (2, 1, 1, 'READ', 'MODE BACA', 'Kenapa Sekolah Punya Aturan?', '{"paragraphs": ["Sekolah punya tata tertib supaya kegiatan belajar berjalan aman, nyaman, dan adil untuk semua siswa.", "Contoh tata tertib: datang tepat waktu, memakai seragam, dan menjaga sopan santun."]}'::jsonb, 'Aturan membuat sekolah nyaman!'),
  (2, 1, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Apa tujuan sekolah memiliki tata tertib?", "options": [{"text": "Supaya siswa takut", "correct": false}, {"text": "Supaya kegiatan belajar aman dan tertib", "correct": true}, {"text": "Supaya guru bisa menghukum", "correct": false}, {"text": "Supaya sekolah terlihat keren", "correct": false}], "feedbackCorrect": "Benar! Tata tertib membuat belajar jadi aman dan tertib.", "feedbackWrong": "Kurang tepat. Tata tertib dibuat supaya kegiatan belajar aman dan tertib."}'::jsonb, 'Pilih jawabanmu!'),
  (2, 2, 1, 'READ', 'MODE BACA', 'Wajib Belajar', '{"paragraphs": ["Menurut UU Sistem Pendidikan Nasional (UU No. 20 Tahun 2003), setiap warga negara berusia 7 sampai 15 tahun wajib mengikuti pendidikan dasar.", "Pendidikan dasar adalah SD dan SMP. Pemerintah juga wajib menyediakan pendidikan dasar ini."]}'::jsonb, 'Belajar itu hak sekaligus kewajiban!'),
  (2, 2, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Menurut UU Sisdiknas, usia berapa yang wajib mengikuti pendidikan dasar?", "options": [{"text": "5 sampai 10 tahun", "correct": false}, {"text": "7 sampai 15 tahun", "correct": true}, {"text": "10 sampai 18 tahun", "correct": false}, {"text": "Semua usia", "correct": false}], "feedbackCorrect": "Benar! Usia 7 sampai 15 tahun wajib mengikuti pendidikan dasar.", "feedbackWrong": "Kurang tepat. Jawaban yang benar: 7 sampai 15 tahun."}'::jsonb, 'Pilih jawabanmu!'),
  (2, 3, 1, 'READ', 'MODE BACA', 'Stop Perundungan', '{"paragraphs": ["Perundungan (bullying) adalah menyakiti orang lain berulang kali, misalnya mengejek, mendorong, atau mengucilkan.", "Kekerasan di sekolah dilarang. Sekolah wajib mencegah dan menangani kekerasan, termasuk perundungan.", "Jika kamu melihat atau mengalami perundungan, laporkan kepada guru atau orang tua."]}'::jsonb, 'Berani melapor itu hebat!'),
  (2, 3, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Kamu melihat temanmu terus diejek oleh kakak kelas. Apa yang sebaiknya kamu lakukan?", "options": [{"text": "Ikut mengejek", "correct": false}, {"text": "Diam saja", "correct": false}, {"text": "Melaporkannya kepada guru", "correct": true}, {"text": "Merekam lalu menyebarkannya", "correct": false}], "feedbackCorrect": "Benar! Melapor kepada guru membantu menghentikan perundungan.", "feedbackWrong": "Kurang tepat. Sebaiknya laporkan kepada guru."}'::jsonb, 'Pilih jawabanmu!'),
  (2, 4, 1, 'READ', 'MODE BACA', 'Menjaga Fasilitas Sekolah', '{"paragraphs": ["Meja, kursi, buku perpustakaan, dan toilet sekolah dipakai bersama. Kita wajib menjaganya.", "Merusak fasilitas sekolah merugikan semua orang dan bisa mendapat sanksi sesuai tata tertib."]}'::jsonb, 'Fasilitas sekolah milik bersama!'),
  (2, 4, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Apa contoh menjaga fasilitas sekolah?", "options": [{"text": "Mencoret-coret meja", "correct": false}, {"text": "Mengembalikan buku perpustakaan tepat waktu", "correct": true}, {"text": "Membuang sampah di laci", "correct": false}, {"text": "Membanting pintu kelas", "correct": false}], "feedbackCorrect": "Benar! Itu cara menjaga fasilitas sekolah.", "feedbackWrong": "Kurang tepat. Jawaban yang benar: mengembalikan buku perpustakaan tepat waktu."}'::jsonb, 'Pilih jawabanmu!'),
  (2, 5, 1, 'QUIZ', 'MODE KUIS', null, '{"question": "Datang terlambat ke sekolah berarti...", "options": [{"text": "Melanggar tata tertib", "correct": true}, {"text": "Menjalankan hak", "correct": false}, {"text": "Tidak apa-apa", "correct": false}, {"text": "Mendapat hadiah", "correct": false}], "feedbackCorrect": "Benar!", "feedbackWrong": "Kurang tepat. Datang terlambat melanggar tata tertib."}'::jsonb, 'Latihan dimulai!'),
  (2, 5, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Pendidikan dasar terdiri dari...", "options": [{"text": "TK dan SD", "correct": false}, {"text": "SD dan SMP", "correct": true}, {"text": "SMP dan SMA", "correct": false}, {"text": "SMA dan kuliah", "correct": false}], "feedbackCorrect": "Benar! Pendidikan dasar adalah SD dan SMP.", "feedbackWrong": "Kurang tepat. Pendidikan dasar adalah SD dan SMP."}'::jsonb, 'Pilih jawabanmu!'),
  (2, 5, 3, 'QUIZ', 'MODE KUIS', null, '{"question": "Mengejek teman berulang kali termasuk...", "options": [{"text": "Bercanda biasa", "correct": false}, {"text": "Perundungan", "correct": true}, {"text": "Kewajiban", "correct": false}, {"text": "Hak berpendapat", "correct": false}], "feedbackCorrect": "Benar! Itu perundungan dan tidak boleh dilakukan.", "feedbackWrong": "Kurang tepat. Itu termasuk perundungan."}'::jsonb, 'Pilih jawabanmu!'),
  (3, 1, 1, 'READ', 'MODE BACA', 'Keluarga Itu Apa?', '{"paragraphs": ["Keluarga adalah kelompok terkecil dalam masyarakat, biasanya terdiri dari ayah, ibu, dan anak.", "Setiap anggota keluarga punya peran: orang tua mengasuh dan melindungi, anak menghormati dan membantu orang tua."]}'::jsonb, 'Keluarga adalah rumah pertama kita!'),
  (3, 1, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Apa peran anak dalam keluarga?", "options": [{"text": "Menghormati dan membantu orang tua", "correct": true}, {"text": "Mencari nafkah untuk keluarga", "correct": false}, {"text": "Membayar tagihan listrik", "correct": false}, {"text": "Mengatur keuangan keluarga", "correct": false}], "feedbackCorrect": "Benar! Anak menghormati dan membantu orang tua.", "feedbackWrong": "Kurang tepat. Anak berperan menghormati dan membantu orang tua."}'::jsonb, 'Pilih jawabanmu!'),
  (3, 2, 1, 'READ', 'MODE BACA', 'Akta Kelahiran', '{"paragraphs": ["Setiap anak berhak atas identitas diri, yaitu nama dan kewarganegaraan.", "Identitas anak dicatat dalam akta kelahiran. Akta kelahiran dibutuhkan untuk banyak hal, misalnya mendaftar sekolah."]}'::jsonb, 'Identitas itu hakmu!'),
  (3, 2, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Dokumen apa yang mencatat identitas dan kelahiran seorang anak?", "options": [{"text": "Rapor", "correct": false}, {"text": "Akta kelahiran", "correct": true}, {"text": "Kartu perpustakaan", "correct": false}, {"text": "Surat izin sakit", "correct": false}], "feedbackCorrect": "Benar! Akta kelahiran mencatat identitas anak.", "feedbackWrong": "Kurang tepat. Jawaban yang benar: akta kelahiran."}'::jsonb, 'Pilih jawabanmu!'),
  (3, 3, 1, 'READ', 'MODE BACA', 'Tugas Orang Tua', '{"paragraphs": ["Menurut UU Perlindungan Anak, orang tua wajib mengasuh, memelihara, mendidik, dan melindungi anak.", "Orang tua juga wajib mencegah anak menikah terlalu muda."]}'::jsonb, 'Orang tua menjaga kita!'),
  (3, 3, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Manakah yang termasuk kewajiban orang tua kepada anak?", "options": [{"text": "Menyuruh anak berhenti sekolah", "correct": false}, {"text": "Mendidik dan melindungi anak", "correct": true}, {"text": "Membiarkan anak tanpa pengawasan", "correct": false}, {"text": "Menyuruh anak bekerja berat", "correct": false}], "feedbackCorrect": "Benar! Orang tua wajib mendidik dan melindungi anak.", "feedbackWrong": "Kurang tepat. Orang tua wajib mendidik dan melindungi anak."}'::jsonb, 'Pilih jawabanmu!'),
  (3, 4, 1, 'READ', 'MODE BACA', 'Batas Usia Menikah', '{"paragraphs": ["Menurut UU No. 16 Tahun 2019 tentang perubahan UU Perkawinan, laki-laki dan perempuan baru boleh menikah jika sudah berusia 19 tahun.", "Aturan ini melindungi anak supaya bisa terus sekolah dan tumbuh dengan sehat."]}'::jsonb, 'Sekolah dulu, ya!'),
  (3, 4, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Berapa usia minimal untuk menikah menurut UU No. 16 Tahun 2019?", "options": [{"text": "15 tahun", "correct": false}, {"text": "17 tahun", "correct": false}, {"text": "19 tahun", "correct": true}, {"text": "21 tahun", "correct": false}], "feedbackCorrect": "Benar! Usia minimal menikah adalah 19 tahun.", "feedbackWrong": "Kurang tepat. Usia minimal menikah adalah 19 tahun."}'::jsonb, 'Pilih jawabanmu!'),
  (3, 5, 1, 'QUIZ', 'MODE KUIS', null, '{"question": "Untuk mendaftar sekolah, dokumen apa yang biasanya dibutuhkan?", "options": [{"text": "Akta kelahiran", "correct": true}, {"text": "SIM", "correct": false}, {"text": "Paspor kakek", "correct": false}, {"text": "Tiket kereta", "correct": false}], "feedbackCorrect": "Benar!", "feedbackWrong": "Kurang tepat. Akta kelahiran biasanya dibutuhkan."}'::jsonb, 'Latihan dimulai!'),
  (3, 5, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Mengasuh dan melindungi anak adalah kewajiban...", "options": [{"text": "Teman sekelas", "correct": false}, {"text": "Orang tua", "correct": true}, {"text": "Tetangga saja", "correct": false}, {"text": "Anak itu sendiri", "correct": false}], "feedbackCorrect": "Benar!", "feedbackWrong": "Kurang tepat. Itu kewajiban orang tua."}'::jsonb, 'Pilih jawabanmu!'),
  (3, 5, 3, 'QUIZ', 'MODE KUIS', null, '{"question": "Seorang anak berusia 16 tahun dipaksa menikah. Apakah ini sesuai hukum?", "options": [{"text": "Ya, sesuai hukum", "correct": false}, {"text": "Tidak, usia minimal menikah 19 tahun", "correct": true}, {"text": "Ya, jika orang tua setuju saja", "correct": false}, {"text": "Ya, jika sudah lulus SD", "correct": false}], "feedbackCorrect": "Benar! Usia minimal menikah adalah 19 tahun.", "feedbackWrong": "Kurang tepat. Usia minimal menikah adalah 19 tahun."}'::jsonb, 'Pilih jawabanmu!'),
  (4, 1, 1, 'READ', 'MODE BACA', 'Rambu dan Lampu Lalu Lintas', '{"paragraphs": ["Jalan raya punya aturan supaya semua orang aman. Rambu dan lampu lalu lintas adalah tandanya.", "Lampu merah artinya berhenti, kuning artinya hati-hati, dan hijau artinya boleh jalan. Pejalan kaki menyeberang di zebra cross saat lampu pejalan kaki berwarna hijau."]}'::jsonb, 'Ayo kita lanjut!'),
  (4, 1, 2, 'EXAMPLES', 'MODE BACA', 'Menyeberang dengan Aman', '{"examples": [{"label": "CONTOH BAIK", "tone": "GOOD", "caption": "Lampu pejalan kaki hijau. Anak menyeberang di zebra cross.", "illustration": "CROSSING_GREEN"}, {"label": "CONTOH BURUK", "tone": "BAD", "caption": "Lampu pejalan kaki merah, tetapi anak tetap menyeberang. Berbahaya!", "illustration": "CROSSING_RED_CAR"}]}'::jsonb, 'Perhatikan lampunya ya!'),
  (4, 1, 3, 'QUIZ', 'MODE KUIS', null, '{"question": "Kamu ingin menyeberang jalan, tetapi lampu pejalan kaki berwarna merah. Apa yang harus kamu lakukan?", "options": [{"text": "Berlari cepat menyeberang", "correct": false}, {"text": "Menunggu sampai lampu pejalan kaki hijau", "correct": true}, {"text": "Menyeberang sambil bermain HP", "correct": false}, {"text": "Mengikuti teman yang sudah menyeberang", "correct": false}], "feedbackCorrect": "Benar! Tunggu lampu pejalan kaki hijau sebelum menyeberang.", "feedbackWrong": "Kurang tepat. Jawaban yang benar: tunggu sampai lampu pejalan kaki hijau."}'::jsonb, 'Pilih jawabanmu!'),
  (4, 2, 1, 'READ', 'MODE BACA', 'Pakai Helm!', '{"paragraphs": ["Menurut UU Lalu Lintas dan Angkutan Jalan (UU No. 22 Tahun 2009), pengemudi dan penumpang sepeda motor wajib memakai helm yang memenuhi Standar Nasional Indonesia (SNI).", "Helm melindungi kepala jika terjadi kecelakaan. Jadi, walaupun jaraknya dekat, tetap pakai helm."]}'::jsonb, 'Kepala kita berharga!'),
  (4, 2, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Siapa yang wajib memakai helm saat naik sepeda motor?", "options": [{"text": "Hanya pengemudi", "correct": false}, {"text": "Hanya penumpang", "correct": false}, {"text": "Pengemudi dan penumpang", "correct": true}, {"text": "Tidak ada, jika jaraknya dekat", "correct": false}], "feedbackCorrect": "Benar! Pengemudi dan penumpang wajib memakai helm.", "feedbackWrong": "Kurang tepat. Pengemudi dan penumpang sama-sama wajib memakai helm."}'::jsonb, 'Pilih jawabanmu!'),
  (4, 3, 1, 'READ', 'MODE BACA', 'SIM dan Batas Usia', '{"paragraphs": ["Untuk mengemudikan kendaraan bermotor di jalan, seseorang wajib memiliki Surat Izin Mengemudi (SIM).", "Usia minimal untuk membuat SIM A (mobil) dan SIM C (sepeda motor) adalah 17 tahun. Jadi, anak SD dan SMP belum boleh mengendarai motor sendiri di jalan raya."]}'::jsonb, 'Tunggu sampai cukup umur, ya!'),
  (4, 3, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Berapa usia minimal untuk membuat SIM C (sepeda motor)?", "options": [{"text": "12 tahun", "correct": false}, {"text": "15 tahun", "correct": false}, {"text": "17 tahun", "correct": true}, {"text": "21 tahun", "correct": false}], "feedbackCorrect": "Benar! Usia minimal membuat SIM C adalah 17 tahun.", "feedbackWrong": "Kurang tepat. Usia minimal membuat SIM C adalah 17 tahun."}'::jsonb, 'Pilih jawabanmu!'),
  (4, 4, 1, 'QUIZ', 'MODE KUIS', null, '{"question": "Lampu lalu lintas berwarna kuning artinya...", "options": [{"text": "Boleh ngebut", "correct": false}, {"text": "Hati-hati", "correct": true}, {"text": "Berhenti total selamanya", "correct": false}, {"text": "Boleh parkir", "correct": false}], "feedbackCorrect": "Benar!", "feedbackWrong": "Kurang tepat. Kuning artinya hati-hati."}'::jsonb, 'Latihan dimulai!'),
  (4, 4, 2, 'QUIZ', 'MODE KUIS', null, '{"question": "Di mana tempat yang aman untuk menyeberang jalan?", "options": [{"text": "Di tikungan", "correct": false}, {"text": "Di zebra cross", "correct": true}, {"text": "Di antara mobil yang parkir", "correct": false}, {"text": "Di mana saja", "correct": false}], "feedbackCorrect": "Benar! Menyeberanglah di zebra cross.", "feedbackWrong": "Kurang tepat. Tempat yang aman adalah zebra cross."}'::jsonb, 'Pilih jawabanmu!'),
  (4, 4, 3, 'QUIZ', 'MODE KUIS', null, '{"question": "Andi kelas 8 SMP ingin mengendarai motor ke sekolah sendirian. Bolehkah?", "options": [{"text": "Boleh, asal pakai helm", "correct": false}, {"text": "Tidak boleh, karena belum cukup umur untuk SIM", "correct": true}, {"text": "Boleh, jika jalannya sepi", "correct": false}, {"text": "Boleh, jika diizinkan teman", "correct": false}], "feedbackCorrect": "Benar! Andi belum cukup umur untuk memiliki SIM.", "feedbackWrong": "Kurang tepat. Andi belum cukup umur untuk memiliki SIM."}'::jsonb, 'Pilih jawabanmu!');

-- ======================================================== Part 2: demo users
-- Passwords: budi@legaloo.id / legaloo123, siti.rahma@gmail.com / hukum2026 (bcrypt, cost 12)
delete from users where lower(email) in ('budi@legaloo.id', 'siti.rahma@gmail.com');

insert into users (id, name, email, password_hash, daily_goal_minutes) values
  ('11111111-1111-4111-8111-111111111111', 'Budi Santoso',   'budi@legaloo.id',      '$2b$12$qOSwwJsxUngmDP9iip4Q/.8JOOqh/asT7fsDW.z5z/I37pB5/KL6u', 10),
  ('22222222-2222-4222-8222-222222222222', 'Siti Rahmawati', 'siti.rahma@gmail.com', '$2b$12$rgBXwNyhqY7FscsNe3v3Z.WbXwMPUrR9AlMoCqb9MqLfS7FIEaY36', 10);

-- Budi mirrors the app's DummyData: course 1 levels 1-2 done (level 3 ACTIVE), course 2 level 1 done.
-- Most recent completion is in course 1, so course 1 is his current course (Unit 2).
insert into level_completions (user_id, course_id, level_position, correct, completed_at) values
  ('11111111-1111-4111-8111-111111111111', 2, 1, true, now() - interval '5 days'),
  ('11111111-1111-4111-8111-111111111111', 1, 1, true, now() - interval '3 days'),
  ('11111111-1111-4111-8111-111111111111', 1, 2, true, now() - interval '1 day');

-- Budi: goal met on each of the previous 7 days, 6 of 10 minutes today -> streak 7, bar 6/10.
insert into study_log (user_id, study_date, minutes)
select '11111111-1111-4111-8111-111111111111',
       (now() at time zone 'Asia/Jakarta')::date - d,
       case when d = 0 then 6 else 12 end
from generate_series(0, 7) as d;

-- Siti is a fresh account: no completions, no study log (every course starts at level 1).

commit;
