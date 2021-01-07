#include <filesystem>
#include <sstream>
#include <vector>
#include <string>
#include <mutex>
#include <vector>
#include <string_view>
#include <fstream>
#include <thread>
namespace fs = std::filesystem;

namespace os {
	class path {
	public:
		path() = default;
		std::vector<std::string> listdir(const fs::path& path) {
			std::vector<std::string> dirList;
			dirList.reserve(10);
			for (auto& file : fs::directory_iterator(path)) {
				dirList.emplace_back(file.path().relative_path().string());
				if (dirList.capacity() == dirList.size())
					dirList.reserve(10);
			}
			dirList.shrink_to_fit();
			return dirList;
		}
	};
}
class sharedResource {
public:
	sharedResource() {
		outputFile1.open(path1, std::ios_base::out);
		outputFile2.open(path2, std::ios_base::out);
	}
	void write(std::string_view file1, std::string_view file2) {
		std::lock_guard<std::mutex> guard(mut);
		outputFile1 << file1;
		outputFile2 << file2;
	}
	void print() {
		if (outputFile1.is_open() && outputFile2.is_open()) {
			outputFile1 << output1.str();
			outputFile2 << output2.str();
		}
		outputFile1.close();
		outputFile2.close();
	}
private:
	std::mutex mut;
	std::ostringstream output1, output2;
	std::fstream outputFile1, outputFile2;
	std::string path1 = R"(songpath.txt)",
		path2 = R"(songfile.txt)";
};
auto resource = sharedResource();

void searchDrive(fs::path folder)
{
	auto isFile = [](const fs::path file) {return file.filename().extension() == ".mp3"; };
	std::ostringstream threadIO1, threadIO2;
	try {
		if (fs::exists(folder) && fs::is_directory(folder))
		{
			for (auto const& entry : fs::recursive_directory_iterator(folder, fs::directory_options::skip_permission_denied)) {
				try {
					if (isFile(entry)) {
						threadIO1 << entry.path().filename().string() << "\n";
						threadIO2 << entry.path().parent_path().string() << "\n";
					}
				}
				catch (fs::filesystem_error const& error) {}
				catch (std::exception const& error) {}
			}
			resource.write(threadIO2.str(), threadIO1.str());
		}
	}
	catch (fs::filesystem_error const& error) {}
	catch (std::exception const& error) {}
}
int main() {
	fs::path rootFolder = "C:\\";
	auto list = os::path().listdir(rootFolder);
	std::vector<std::thread> thread_list;
	thread_list.reserve(std::size(list));
	auto counter{ 0 };

	for (auto &folder : list) {
		if (folder == "Windows")
			continue;
		else {
			thread_list.emplace_back(std::thread(searchDrive, rootFolder.string() + folder));
		}
	}

	for (auto& thread : thread_list) {
		thread.join();
	}
	resource.print();
}