// c++ -std=c++17 -o env-var-path-search env-var-path-search.cpp

#include <cstring>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

void help() {
    std::cout << "Usage: env-var-dir-search ENVVAR [SUBSTRING]" << std::endl;
    std::cout << "Searches the colon-separated list of directories in PATH for files with "
                 "filenames containing SUBSTRING (if provided)."
              << std::endl;
    std::cout << "If SUBSTRING is not provided, all files in ENVVAR are printed." << std::endl;
}

int main(int argc, char *argv[]) {
    // Display usage message if the --help option is specified
    if (argc == 2 && std::strcmp(argv[1], "--help") == 0) {
        help();
        return 0;
    }

    // Check that the correct number of arguments was provided
    if (argc < 2) {
        std::cerr << "Error: Incorrect number of arguments." << std::endl;
        help();
        return 1;
    }

    // Get the list of directories to search from the first argument
    std::string envvar_str;
    if (const char *env_p = std::getenv(argv[1])) {
        envvar_str = env_p;
    } else {
        std::cerr << "Error: Unable to get environment variable '" << envvar_str << "."
                  << std::endl;
        return 2;
    }

    // Split the list of directories into a vector
    std::vector<std::string> directories;
    std::istringstream path_stream(envvar_str);
    std::string directory;
    while (std::getline(path_stream, directory, ':')) {
        directories.push_back(directory);
    }

    // Get the substring to search for from the second argument (if provided)
    std::string substring;
    if (argc >= 3) {
        substring = argv[2];
    }

    // Search each directory for files with filenames containing the specified substring
    for (const auto &directory : directories) {
        if (!std::filesystem::exists(directory)) {
            continue;
        }
        for (const auto &entry : std::filesystem::directory_iterator(directory)) {
            try {
                if (entry.is_regular_file()) {
                    // If a substring was provided, only print files with filenames containing the
                    // substring
                    if (!substring.empty()) {
                        std::string filename = entry.path().filename().string();
                        if (filename.find(substring) == std::string::npos) {
                            continue;
                        }
                    }

                    // Print the path of the file
                    std::cout << entry.path() << std::endl;
                }
            } catch (const std::filesystem::filesystem_error &e) {
                // Do nothing
            }
        }
    }

    return 0;
}
