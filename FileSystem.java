import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.io.ByteArrayOutputStream;
import java.io.ByteArrayInputStream;
import java.io.DataOutputStream;
import java.io.DataInputStream;
import java.io.FilterInputStream;


public class FileSystem {
	private FileSystemParam fsparam;

	/* FAT data structure */
	private short[] fat = new short[fsparam.blocks];
	/* data block */
	private byte[] data_block = new byte[fsparam.block_size];

	/* reads a data block from disk */
	public byte[] readBlock(String file, int block) {
		byte[] record = new byte[fsparam.block_size];
		try {
			RandomAccessFile fileStore = new RandomAccessFile(file, "rw");
			fileStore.seek(block * fsparam.block_size);
			fileStore.read(record, 0, fsparam.block_size);
			fileStore.close();
		} catch (IOException e) {
			e.printStackTrace();
		}

		return record;
	}

	/* writes a data block to disk */
	public void writeBlock(String file, int block, byte[] record) {
		try {
			RandomAccessFile fileStore = new RandomAccessFile(file, "rw");
			fileStore.seek(block * fsparam.block_size);
			fileStore.write(record, 0, fsparam.block_size);
			fileStore.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/* reads the FAT from disk */
	public short[] readFat(String file) {
		short[] record = new short[fsparam.blocks];
		try {
			RandomAccessFile fileStore = new RandomAccessFile(file, "rw");
			fileStore.seek(0);
			for (int i = 0; i < fsparam.blocks; i++)
				record[i] = fileStore.readShort();
			fileStore.close();
		} catch (IOException e) {
			e.printStackTrace();
		}

		return record;
	}

	/* writes the FAT to disk */
	public void writeFat(String file, short[] fat) {
		try {
			RandomAccessFile fileStore = new RandomAccessFile(file, "rw");
			fileStore.seek(0);
			for (int i = 0; i < fsparam.blocks; i++)
				fileStore.writeShort(fat[i]);
			fileStore.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/* reads a directory entry from a directory */
	public DirEntry readDirEntry(int block, int entry) {
		byte[] bytes = readBlock("filesystem.dat", block);
		ByteArrayInputStream bis = new ByteArrayInputStream(bytes);
		DataInputStream in = new DataInputStream(bis);
		DirEntry dir_entry = new DirEntry();

		try {
			in.skipBytes(entry * fsparam.dir_entry_size);

			for (int i = 0; i < 25; i++)
				dir_entry.filename[i] = in.readByte();
			dir_entry.attributes = in.readByte();
			dir_entry.first_block = in.readShort();
			dir_entry.size = in.readInt();
		} catch (IOException e) {
			e.printStackTrace();
		}

		return dir_entry;
	}

	/* writes a directory entry in a directory */
	public void writeDirEntry(int block, int entry, DirEntry dir_entry) {
		byte[] bytes = readBlock("filesystem.dat", block);
		ByteArrayInputStream bis = new ByteArrayInputStream(bytes);
		DataInputStream in = new DataInputStream(bis);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		DataOutputStream out = new DataOutputStream(bos);

		try {
			for (int i = 0; i < entry * fsparam.dir_entry_size; i++)
				out.writeByte(in.readByte());

			for (int i = 0; i < fsparam.dir_entry_size; i++)
				in.readByte();

			for (int i = 0; i < 25; i++)
				out.writeByte(dir_entry.filename[i]);
			out.writeByte(dir_entry.attributes);
			out.writeShort(dir_entry.first_block);
			out.writeInt(dir_entry.size);

			for (int i = entry + 1; i < entry * fsparam.dir_entry_size; i++)
				out.writeByte(in.readByte());
		} catch (IOException e) {
			e.printStackTrace();
		}

		byte[] bytes2 = bos.toByteArray();
		for (int i = 0; i < bytes2.length; i++)
			data_block[i] = bytes2[i];
		writeBlock("filesystem.dat", block, data_block);
	}
	
	
	public void testFileSystem() {
		/* initialize the FAT */
		for (int i = 0; i < fsparam.fat_blocks; i++)
			fat[i] = 0x7ffe;
		fat[fsparam.root_block] = 0x7fff;
		for (int i = fsparam.root_block + 1; i < fsparam.blocks; i++)
			fat[i] = 0;
		/* write it to disk */
		writeFat("filesystem.dat", fat);

		/* initialize an empty data block */
		for (int i = 0; i < fsparam.block_size; i++)
			data_block[i] = 0;

		/* write an empty ROOT directory block */
		writeBlock("filesystem.dat", fsparam.root_block, data_block);

		/* write the remaining data blocks to disk */
		for (int i = fsparam.root_block + 1; i < fsparam.blocks; i++)
			writeBlock("filesystem.dat", i, data_block);

		/* fill three root directory entries and list them */
		DirEntry dir_entry = new DirEntry();
		String name = "file1";
		byte[] namebytes = name.getBytes();
		for (int i = 0; i < namebytes.length; i++)
			dir_entry.filename[i] = namebytes[i];
		dir_entry.attributes = 0x01;
		dir_entry.first_block = 1111;
		dir_entry.size = 222;
		writeDirEntry(fsparam.root_block, 0, dir_entry);

		name = "file2";
		namebytes = name.getBytes();
		for (int i = 0; i < namebytes.length; i++)
			dir_entry.filename[i] = namebytes[i];
		dir_entry.attributes = 0x01;
		dir_entry.first_block = 2222;
		dir_entry.size = 333;
		writeDirEntry(fsparam.root_block, 1, dir_entry);

		name = "file3";
		namebytes = name.getBytes();
		for (int i = 0; i < namebytes.length; i++)
			dir_entry.filename[i] = namebytes[i];
		dir_entry.attributes = 0x01;
		dir_entry.first_block = 3333;
		dir_entry.size = 444;
		writeDirEntry(fsparam.root_block, 2, dir_entry);

		/* list entries from the root directory */
		for (int i = 0; i < fsparam.dir_entries; i++) {
			dir_entry = readDirEntry(fsparam.root_block, i);
			System.out.println("Entry " + i + ", file: " + new String(dir_entry.filename) + " attr: " +
			dir_entry.attributes + " first: " + dir_entry.first_block + " size: " + dir_entry.size);
		}
	}
}
