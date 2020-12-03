#include <filesystem>
#include <sstream>
#include <fstream>
#include <thread>
#include <vector>
#include <string>
using namespace std::literals::chrono_literals;
namespace fs = std::filesystem;
void collectFileName(std::string fileName)
{
	std::fstream outputFile(R"(C:\Users\HP\PycharmProjects\new music player\)" + fileName, std::ios_base::out);
	fs::path inPath = "C:\\";
	auto isFile = [](const fs::path file) {return file.filename().extension() == ".mp3"; };
	std::ostringstream output;
	if (fs::exists(inPath) && fs::is_directory(inPath))
	{
		for (auto const& entry : fs::recursive_directory_iterator(inPath, fs::directory_options::skip_permission_denied)) {
			try {
				if (isFile(entry)) {
					output << entry.path().filename().string() << "\n";
					
				}
			}
			catch (std::filesystem::filesystem_error const& error) {}
			catch (std::exception const& error) {}
		}
	}
	outputFile << output.str();
	outputFile.close();
}
void collectFilePath(std::string fileName)
{
	std::fstream outputFile(R"(C:\Users\HP\PycharmProjects\new music player\)" + fileName, std::ios_base::out);
	fs::path inPath = "C:\\";
	auto isFile = [](const fs::path file) {return file.filename().extension() == ".mp3"; };
	std::ostringstream output;
	if (fs::exists(inPath) && fs::is_directory(inPath))
	{
		for (auto const& entry : fs::recursive_directory_iterator(inPath, fs::directory_options::skip_permission_denied)) {
			try {
				if (isFile(entry)) {
					output << entry.path().parent_path().string() << "\n";
				}
			}
			catch (std::filesystem::filesystem_error const& error) {}
			catch (std::exception const& error) {}
		}
	}
	outputFile << output.str();
	outputFile.close();
}
int main() {
	std::vector<std::thread> fileThreads(2);
	fileThreads.at(0) = (std::thread(collectFileName, std::string{ "songfile.txt" }));
	fileThreads.at(1) = (std::thread(collectFilePath, std::string{ "songpath.txt" }));
	for (auto& thread : fileThreads)
		thread.join();
}