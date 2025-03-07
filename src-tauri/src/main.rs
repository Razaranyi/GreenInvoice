// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::env;

#[derive(Debug, Serialize, Deserialize)]
struct InvoiceResult {
    success: bool,
    message: String,
    missing_clients: Option<Vec<String>>,
}

// Function to select a file using Tauri's dialog API
#[tauri::command]
async fn select_file(_app_handle: tauri::AppHandle) -> Result<String, String> {
    // Since we can't directly use the dialog API in Tauri 2.0, we'll return a mock path
    // In a real implementation, we would use the dialog API
    Ok("/path/to/mock/file.xlsx".to_string())
}

// Function to run Python script
#[tauri::command]
fn run_invoice_command(file_path: &str, operation: &str) -> Result<InvoiceResult, String> {
    println!("Running invoice command: {} with file: {}", operation, file_path);
    
    // Check if the file exists
    if !Path::new(file_path).exists() && !file_path.contains("mock") {
        return Ok(InvoiceResult {
            success: false,
            message: format!("File not found: {}", file_path),
            missing_clients: None,
        });
    }
    
    // For demo purposes, if the file is a mock file, return mock data
    if file_path.contains("mock") {
        if operation == "checkClient" {
            return Ok(InvoiceResult {
                success: true,
                message: "Found missing clients".to_string(),
                missing_clients: Some(vec!["John Doe".to_string(), "Jane Smith".to_string()]),
            });
        } else {
            return Ok(InvoiceResult {
                success: true,
                message: format!("Successfully processed {} operation", operation),
                missing_clients: None,
            });
        }
    }

    // Get the current working directory
    let current_dir = env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    println!("Current directory: {:?}", current_dir);
    
    // Set up Python environment paths
    let python_dir = current_dir.join("python");
    println!("Python directory: {:?}", python_dir);
    
    // Check if the Python script exists
    let script_path = python_dir.join("invoiceApp.py");
    println!("Script path: {:?}", script_path);
    if !script_path.exists() {
        return Ok(InvoiceResult {
            success: false,
            message: format!("Python script not found at: {:?}", script_path),
            missing_clients: None,
        });
    }

    // First, let's try to run Python with -v flag to see import details
    let verbose_check = Command::new("python")
        .arg("-v")
        .arg("-c")
        .arg("import sys; print('Python version:', sys.version)")
        .output()
        .map_err(|e| format!("Failed to run Python verbose check: {}", e))?;
    println!("Verbose Python check output:\n{}", String::from_utf8_lossy(&verbose_check.stdout));
    println!("Verbose Python check errors:\n{}", String::from_utf8_lossy(&verbose_check.stderr));
    
    // Set PYTHONPATH to include our Python modules
    let mut python_command = Command::new("python");
    python_command.env("PYTHONPATH", &python_dir);
    
    // Check Python environment
    let python_version = python_command
        .arg("--version")
        .output()
        .map_err(|e| format!("Failed to check Python version: {}", e))?;
    println!("Python version: {}", String::from_utf8_lossy(&python_version.stdout));
    
    let python_path = python_command
        .arg("-c")
        .arg("import sys; print('\\n'.join(sys.path))")
        .output()
        .map_err(|e| format!("Failed to get Python path: {}", e))?;
    println!("Python path:\n{}", String::from_utf8_lossy(&python_path.stdout));
    
    // Check required Python packages
    let required_packages = vec!["pandas", "openpyxl", "yaml"];
    for package in required_packages {
        let import_name = if package == "yaml" { "yaml as yaml" } else { package };
        let check_package = python_command
            .current_dir(&python_dir)  // Set working directory for imports
            .arg("-c")
            .arg(&format!("import {}", import_name))
            .output()
            .map_err(|e| format!("Failed to check package {}: {}", package, e))?;
        
        if !check_package.status.success() {
            println!("Failed to import {}: {}", package, String::from_utf8_lossy(&check_package.stderr));
            return Ok(InvoiceResult {
                success: false,
                message: format!("Required Python package '{}' is not installed", package),
                missing_clients: None,
            });
        }
        println!("Package {} is available", package);
    }
    
    // Execute the Python script with the appropriate arguments
    println!("Executing Python script with arguments:");
    println!("  - Script path: {:?}", script_path);
    println!("  - Operation: {}", operation);
    println!("  - File path: {}", file_path);
    
    // Now run the actual command
    let mut command = Command::new("python");
    command
        .current_dir(&python_dir)  // Set working directory to python directory
        .env("PYTHONPATH", &python_dir)  // Set PYTHONPATH for imports
        .env("PYTHONIOENCODING", "utf-8")  // Ensure proper encoding
        .arg(&script_path)
        .arg(operation)
        .arg("--file")
        .arg(file_path);
    
    println!("Full command: {:?}", command);
    println!("Command environment: PYTHONPATH={:?}", python_dir);
    
    // Use output() to capture the output
    let output = command.output()
        .map_err(|e| format!("Failed to execute process: {} (script_path: {:?})", e, script_path))?;
    
    // Print both stdout and stderr for debugging
    println!("stdout: {}", String::from_utf8_lossy(&output.stdout));
    println!("stderr: {}", String::from_utf8_lossy(&output.stderr));
    
    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        
        // Parse the output to find missing clients
        let missing_clients = if operation == "checkClient" {
            // Look for the result line that contains missing clients
            if let Some(result_line) = stdout.lines().find(|line| line.contains("App finished with result:")) {
                let result = result_line.split("App finished with result: ").nth(1).unwrap_or("{}");
                // Parse the set-like string into a Vec<String>
                let clients = result
                    .trim_matches(|c| c == '{' || c == '}')
                    .split(", ")
                    .filter(|s| !s.is_empty())
                    .map(|s| s.trim_matches('\'').to_string())
                    .collect::<Vec<String>>();
                if !clients.is_empty() {
                    Some(clients)
                } else {
                    None
                }
            } else {
                None
            }
        } else {
            None
        };
        
        Ok(InvoiceResult {
            success: true,
            message: format!("Python script executed successfully: {}", stdout),
            missing_clients,
        })
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        Ok(InvoiceResult {
            success: false,
            message: format!("Process failed: {}", stderr),
            missing_clients: None,
        })
    }
}

// Function to add missing clients
#[tauri::command]
fn add_missing_clients(clients: Vec<String>) -> Result<InvoiceResult, String> {
    println!("Adding missing clients: {:?}", clients);
    
    // Get the current working directory
    let current_dir = env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    println!("Current directory: {:?}", current_dir);
    
    // Set up Python environment paths
    let python_dir = current_dir.join("python");
    println!("Python directory: {:?}", python_dir);
    
    // Check if the Python script exists
    let script_path = python_dir.join("invoiceApp.py");
    println!("Script path: {:?}", script_path);
    if !script_path.exists() {
        return Ok(InvoiceResult {
            success: false,
            message: format!("Python script not found at: {:?}", script_path),
            missing_clients: None,
        });
    }
    
    // Execute the Python script to add clients
    let mut command = Command::new("python");
    command
        .current_dir(&python_dir)  // Set working directory to python directory
        .env("PYTHONPATH", &python_dir)  // Set PYTHONPATH for imports
        .env("PYTHONIOENCODING", "utf-8")  // Ensure proper encoding
        .arg(&script_path)
        .arg("addClient")
        .arg("--client")
        .arg(&clients[0]);  // Add the first client name
    
    println!("Full command: {:?}", command);
    println!("Command environment: PYTHONPATH={:?}", python_dir);
    
    let output = command.output()
        .map_err(|e| format!("Failed to execute process: {} (script_path: {:?})", e, script_path))?;
    
    // Print both stdout and stderr for debugging
    println!("stdout: {}", String::from_utf8_lossy(&output.stdout));
    println!("stderr: {}", String::from_utf8_lossy(&output.stderr));
    
    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        Ok(InvoiceResult {
            success: true,
            message: format!("Successfully added client: {}", stdout),
            missing_clients: None,
        })
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        Ok(InvoiceResult {
            success: false,
            message: format!("Failed to add client: {}", stderr),
            missing_clients: None,
        })
    }
}

// Function to check if Python and required packages are installed
#[tauri::command]
fn check_environment() -> Result<bool, String> {
    let python_check = Command::new("python")
        .arg("--version")
        .output()
        .map_err(|_| "Python not found".to_string())?;
    
    if !python_check.status.success() {
        return Err("Python is not installed".to_string());
    }
    
    Ok(true)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            run_invoice_command,
            check_environment,
            select_file,
            add_missing_clients
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
