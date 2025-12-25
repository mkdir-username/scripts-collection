/**
 * Jinjava CLI Renderer for SDUI Templates
 *
 * Usage: java -jar jinjava-renderer.jar <template> <data.json> [--output <file>]
 *
 * Renders Jinja2 template using Jinjava (Java implementation).
 * Output goes to stdout unless --output is specified.
 */
package com.alfa.sdui;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hubspot.jinjava.Jinjava;
import com.hubspot.jinjava.JinjavaConfig;
import com.hubspot.jinjava.interpret.RenderResult;
import com.hubspot.jinjava.interpret.TemplateError;
import com.hubspot.jinjava.loader.FileLocator;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.List;

public class JinjavaRenderer {

    private static final String VERSION = "1.0.0";

    public static void main(String[] args) {
        if (args.length < 2) {
            printUsage();
            System.exit(1);
        }

        String templatePath = null;
        String dataPath = null;
        String outputPath = null;
        boolean strictMode = true;

        // Parse arguments
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--help":
                case "-h":
                    printUsage();
                    System.exit(0);
                    break;
                case "--version":
                case "-v":
                    System.out.println("jinjava-renderer " + VERSION);
                    System.exit(0);
                    break;
                case "--output":
                case "-o":
                    if (i + 1 < args.length) {
                        outputPath = args[++i];
                    } else {
                        System.err.println("Error: --output requires a path argument");
                        System.exit(1);
                    }
                    break;
                case "--lenient":
                    strictMode = false;
                    break;
                default:
                    if (templatePath == null) {
                        templatePath = args[i];
                    } else if (dataPath == null) {
                        dataPath = args[i];
                    }
                    break;
            }
        }

        if (templatePath == null || dataPath == null) {
            System.err.println("Error: Both template and data paths are required");
            printUsage();
            System.exit(1);
        }

        try {
            String result = render(templatePath, dataPath, strictMode);

            if (outputPath != null) {
                Files.write(Paths.get(outputPath), result.getBytes(StandardCharsets.UTF_8));
                System.err.println("Output written to: " + outputPath);
            } else {
                System.out.println(result);
            }

        } catch (RenderException e) {
            System.err.println("RENDER_ERROR: " + e.getMessage());
            if (e.getErrors() != null) {
                for (String error : e.getErrors()) {
                    System.err.println("  - " + error);
                }
            }
            System.exit(2);
        } catch (IOException e) {
            System.err.println("IO_ERROR: " + e.getMessage());
            System.exit(3);
        } catch (Exception e) {
            System.err.println("ERROR: " + e.getClass().getSimpleName() + ": " + e.getMessage());
            System.exit(4);
        }
    }

    public static String render(String templatePath, String dataPath, boolean strictMode)
            throws IOException, RenderException {

        // Load template
        Path tplPath = Paths.get(templatePath).toAbsolutePath();
        if (!Files.exists(tplPath)) {
            throw new IOException("Template not found: " + templatePath);
        }
        String template = Files.readString(tplPath, StandardCharsets.UTF_8);
        File templateDir = tplPath.getParent().toFile();

        // Load data
        Path dPath = Paths.get(dataPath).toAbsolutePath();
        if (!Files.exists(dPath)) {
            throw new IOException("Data file not found: " + dataPath);
        }

        ObjectMapper mapper = new ObjectMapper();
        Map<String, Object> context = mapper.readValue(
            dPath.toFile(),
            new TypeReference<Map<String, Object>>() {}
        );

        // Add JSON-safe globals (like Python version)
        context.putIfAbsent("null", null);
        context.putIfAbsent("none", null);  // Python keyword compatibility
        context.putIfAbsent("true", true);
        context.putIfAbsent("false", false);

        // Configure Jinjava
        JinjavaConfig config = JinjavaConfig.newBuilder()
            .withTrimBlocks(true)
            .withLstripBlocks(true)
            .withFailOnUnknownTokens(strictMode)
            .withMaxRenderDepth(20)
            .build();

        Jinjava jinjava = new Jinjava(config);

        // Register custom filters
        jinjava.getGlobalContext().registerFilter(new ToJsonFilter());

        // Set up file locator for includes
        try {
            jinjava.setResourceLocator(new FileLocator(templateDir));
        } catch (Exception e) {
            // FileLocator may not be available in all versions
            System.err.println("Warning: FileLocator not available, includes may not work");
        }

        // Render
        RenderResult result = jinjava.renderForResult(template, context);

        // Check for errors
        List<TemplateError> errors = result.getErrors();
        if (!errors.isEmpty()) {
            boolean hasFatal = errors.stream()
                .anyMatch(e -> e.getSeverity() == TemplateError.ErrorType.FATAL);

            if (hasFatal) {
                String[] errorMessages = errors.stream()
                    .filter(e -> e.getSeverity() == TemplateError.ErrorType.FATAL)
                    .map(e -> formatError(e))
                    .toArray(String[]::new);
                throw new RenderException("Template rendering failed", errorMessages);
            }

            // Print warnings to stderr
            for (TemplateError error : errors) {
                if (error.getSeverity() == TemplateError.ErrorType.WARNING) {
                    System.err.println("WARNING: " + formatError(error));
                }
            }
        }

        return result.getOutput();
    }

    private static String formatError(TemplateError error) {
        StringBuilder sb = new StringBuilder();
        sb.append(error.getMessage());
        if (error.getLineno() > 0) {
            sb.append(" (line ").append(error.getLineno()).append(")");
        }
        if (error.getFieldName() != null && !error.getFieldName().isEmpty()) {
            sb.append(" [").append(error.getFieldName()).append("]");
        }
        return sb.toString();
    }

    private static void printUsage() {
        System.err.println("Jinjava CLI Renderer v" + VERSION);
        System.err.println();
        System.err.println("Usage: java -jar jinjava-renderer.jar <template> <data.json> [options]");
        System.err.println();
        System.err.println("Arguments:");
        System.err.println("  template       Path to Jinja2/Jinjava template file");
        System.err.println("  data.json      Path to JSON data file");
        System.err.println();
        System.err.println("Options:");
        System.err.println("  -o, --output   Write output to file instead of stdout");
        System.err.println("  --lenient      Don't fail on unknown tokens");
        System.err.println("  -h, --help     Show this help");
        System.err.println("  -v, --version  Show version");
    }

    static class RenderException extends Exception {
        private final String[] errors;

        public RenderException(String message, String[] errors) {
            super(message);
            this.errors = errors;
        }

        public String[] getErrors() {
            return errors;
        }
    }
}
