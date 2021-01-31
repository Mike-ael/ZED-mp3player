#include <filesystem>
#include <sstream>
#include <vector>
#include <string>
#include <mutex>
#include <vector>
#include <fstream>
#include <thread>
#include <algorithm>
namespace fs = std::filesystem;
class sharedResource {
public:
	sharedResource() {
		outputFile1.open(path1, std::ios_base::out);	
		outputFile2.open(path2, std::ios_base::out);
	}
	void write(std::vector<std::string> vecStr1, std::vector<std::string> vecStr2) {
		std::lock_guard<std::mutex> guard(mut);
		//std::sort(std::begin(vecStr1), std::end(vecStr1));
		//std::sort(std::begin(vecStr2), std::end(vecStr2));
		if (outputFile1.is_open() && outputFile2.is_open()) {
			auto [outputPath, outputFilename] = std::pair(std::ostream_iterator<std::string>(outputFile1), std::ostream_iterator<std::string>(outputFile2));
			std::copy(std::cbegin(vecStr2), std::cend(vecStr2), outputPath);
			std::copy(std::cbegin(vecStr1), std::cend(vecStr1), outputFilename);
		}
	}
	~sharedResource() {
		outputFile1.close();
		outputFile2.close();
	}
private:
	std::mutex mut;
	std::fstream outputFile1, outputFile2;
	std::string path1 = R"(songpath.txt)",
		path2 = R"(songfile.txt)";
};
auto resource = sharedResource();

void searchDrive(fs::path folder)
{
	auto isFile = [](const fs::path file) {return file.filename().extension() == ".mp3"; };
	std::vector<std::string> pathVec, fileNamevec;
	pathVec.reserve(500);
	fileNamevec.reserve(500);
	try {
		if (fs::exists(folder) && fs::is_directory(folder))
		{
			for (auto const& entry : fs::recursive_directory_iterator(folder, fs::directory_options::skip_permission_denied)) {
				try {
					if (isFile(entry)) {
						if(pathVec.capacity() == std::size(pathVec))
							pathVec.reserve(50);
							fileNamevec.reserve(50);
						pathVec.emplace_back(entry.path().filename().string() + "\n");
						fileNamevec.emplace_back(entry.path().parent_path().string() + "\n");
					}
				}
				catch (fs::filesystem_error const&) {}
				catch (std::exception const&) {}
			}
			resource.write(pathVec, fileNamevec);
		}
	}
	catch (fs::filesystem_error const&) {}
	catch (std::exception const&) {}
}
int main() {
	std::vector<fs::path> folders{ R"(C:\Users\HP\Music\my music)" , R"(C:\Users\HP\Music\music)" };
	std::vector<std::thread> thread_list;
	thread_list.reserve(std::size(folders));
	std::for_each(std::cbegin(folders), std::cend(folders), [&thread_list](fs::path folder) {
		thread_list.emplace_back(std::thread(searchDrive, folder));
		});
	for (auto& thread : thread_list) {
		thread.join();
	}
}