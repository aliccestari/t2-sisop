public class FileSystemParam {
	public static int block_size = 1024;
	public static int blocks = 2048;
	public static int fat_size = blocks * 2;
	public static int fat_blocks = fat_size / block_size;
	public static int root_block = fat_blocks;
	public static int dir_entry_size = 32;
	public static int dir_entries = block_size / dir_entry_size;
}
