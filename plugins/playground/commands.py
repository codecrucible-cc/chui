import time
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from chui.commands import BaseCommand, CommandContext, NamespacedCommand


class PlaygroundCommand(BaseCommand):
    """Main playground demo command"""

    @property
    def name(self) -> str:
        return "playground"

    def run(self, context: CommandContext) -> Any:
        """Execute the playground command"""
        # Get debug setting
        debug = self.config.get('system.debug', False)

        if debug:
            self.ui.debug(f"Executing playground command")
            self.ui.debug(f"Args: {context.args}")
        
        # Display welcome panel
        self._display_welcome()
        
        # Display available demos
        self._display_demos()
        
        # Emit event for starting playground - using events manager directly
        try:
            # Create an event and emit it through the proper channel
            from chui.events.base import Event
            
            event = Event(
                name="playground.demo_started",
                data={
                    "demo": "playground_main",
                    "timestamp": datetime.now().isoformat()
                },
                timestamp=datetime.now()
            )
            
            # Use the events module from the config if available
            if hasattr(self.config, 'events'):
                self.config.events.emit(event)
            # Alternatively, try through the pipeline
            elif hasattr(self.pipeline, 'event_manager'):
                self.pipeline.event_manager.emit(event)
            # Just log it otherwise
            else:
                if self.config.get('system.debug', False):
                    self.ui.debug(f"Event would be emitted: {event.name}")
        except Exception as e:
            # Silently handle any event emission errors - it's just a demo
            if self.config.get('system.debug', False):
                self.ui.debug(f"Could not emit event: {str(e)}")
        
        return True
        
    def _display_welcome(self) -> None:
        """Display welcome message"""
        welcome_text = """
        Welcome to the CHUI Framework Playground!
        
        This interactive playground demonstrates the various features and capabilities
        of the Command Hub & UI Interface (CHUI) Framework. You can explore different
        UI components, command handling, event systems, and more.
        
        Use the commands below to explore different aspects of the framework.
        """
        
        self.ui.panel(welcome_text, title="CHUI Playground", style="bold blue")
        
    def _display_demos(self) -> None:
        """Display available demos"""
        demos = [
            {"name": "Tables", "command": "tables", "description": "Demonstrates various table display capabilities"},
            {"name": "Forms", "command": "forms", "description": "Shows interactive form input capabilities"},
            {"name": "Panels", "command": "panels", "description": "Displays different panel styles and layouts"},
            {"name": "Pagination", "command": "pagination", "description": "Shows pagination functionality for large datasets"},
            {"name": "Progress", "command": "progress", "description": "Demonstrates progress indicators and animations"},
            {"name": "Colors", "command": "colors", "description": "Shows color capabilities and styling options"}
        ]
        
        # Create table of demos
        headers = ["Demo", "Command", "Description"]
        rows = []
        for demo in demos:
            rows.append([demo["name"], f"demo {demo['command']}", demo["description"]])
            
        self.ui.info("\nAvailable Demos:")
        self.ui.table(headers, rows)
        
        self.ui.info("\nType any demo command to start, for example:")
        self.ui.success("  demo tables")

    def get_help(self) -> str:
        """Get command help text"""
        return """
        CHUI Framework Playground
        
        This command launches the interactive playground that demonstrates
        various features and capabilities of the CHUI Framework.
        
        Usage: playground
        
        Related demo commands:
          demo tables      - Table display capabilities
          demo forms       - Interactive form inputs
          demo panels      - Panel styles and layouts
          demo pagination  - Pagination for large datasets
          demo progress    - Progress indicators
          demo colors      - Color and styling options
        """


class DemoNamespacedCommand(NamespacedCommand):
    """Namespace command for all demos"""
    
    @property
    def name(self) -> str:
        return "demo"
        
    @property
    def namespace(self) -> str:
        return "demo"
        
    @property
    def default_subcommand(self) -> str:
        """Default subcommand when none specified"""
        return "help"
        
    def __init__(self, ui, config, pipeline=None):
        super().__init__(ui, config, pipeline)
        
        # Register subcommands
        self.register_subcommand("tables", self._cmd_tables, "Demonstrate table display capabilities")
        self.register_subcommand("forms", self._cmd_forms, "Demonstrate interactive form capabilities")
        self.register_subcommand("panels", self._cmd_panels, "Demonstrate panel styles and layouts")
        self.register_subcommand("pagination", self._cmd_pagination, "Demonstrate pagination functionality")
        self.register_subcommand("progress", self._cmd_progress, "Demonstrate progress indicators")
        self.register_subcommand("colors", self._cmd_colors, "Demonstrate color capabilities")
        self.register_subcommand("help", self._cmd_help, "Show help for demo commands")
        
        # Register aliases
        self.register_alias("table", "tables")
        self.register_alias("form", "forms")
        self.register_alias("panel", "panels")
        self.register_alias("page", "pagination")
        self.register_alias("color", "colors")
        
    def _cmd_tables(self, context: CommandContext) -> Any:
        """Run tables demo"""
        tables_cmd = TablesCommand(self.ui, self.config, self.pipeline)
        return tables_cmd.run(context)
        
    def _cmd_forms(self, context: CommandContext) -> Any:
        """Run forms demo"""
        forms_cmd = FormsCommand(self.ui, self.config, self.pipeline)
        return forms_cmd.run(context)
        
    def _cmd_panels(self, context: CommandContext) -> Any:
        """Run panels demo"""
        panels_cmd = PanelsCommand(self.ui, self.config, self.pipeline)
        return panels_cmd.run(context)
        
    def _cmd_pagination(self, context: CommandContext) -> Any:
        """Run pagination demo"""
        pagination_cmd = PaginationCommand(self.ui, self.config, self.pipeline)
        return pagination_cmd.run(context)
        
    def _cmd_progress(self, context: CommandContext) -> Any:
        """Run progress demo"""
        progress_cmd = ProgressCommand(self.ui, self.config, self.pipeline)
        return progress_cmd.run(context)
        
    def _cmd_colors(self, context: CommandContext) -> Any:
        """Run colors demo"""
        colors_cmd = ColorsCommand(self.ui, self.config, self.pipeline)
        return colors_cmd.run(context)
        
    def _cmd_help(self, context: CommandContext) -> Any:
        """Show help for demo commands"""
        help_text = """
        CHUI Framework Demo Commands
        
        Usage: demo <command> [options]
        
        Available demo commands:
          tables       - Table display capabilities
          forms        - Interactive form inputs
          panels       - Panel styles and layouts
          pagination   - Pagination for large datasets
          progress     - Progress indicators
          colors       - Color and styling options
          help         - Show this help message
        
        Examples:
          demo tables      - Run the tables demonstration
          demo help        - Show this help message
        """
        self.ui.info(help_text)
        return True


# Common base classes for all demo commands
class TablesCommand(BaseCommand):
    """Demonstrates table display capabilities"""

    @property
    def name(self) -> str:
        return "tables_demo"  # Internal name, not exposed directly

    def run(self, context: CommandContext) -> Any:
        """Execute the tables demo command"""
        self.ui.panel("Table Display Demo", title="CHUI Framework", style="bold green")
        self.ui.info("This demo shows various table display capabilities of the CHUI Framework.\n")
        
        # Simple table demo
        self._demo_simple_table()
        
        # Wait for user input before continuing
        self._wait_for_input("Press Enter to see an advanced table...")
        
        # Advanced table demo
        self._demo_advanced_table()
        
        # Wait for user input before continuing
        self._wait_for_input("Press Enter to see a paginated table...")
        
        # Paginated table demo
        self._demo_paginated_table()
        
        self.ui.success("\nTable demonstration completed!")
        return True
        
    def _demo_simple_table(self) -> None:
        """Demonstrate a simple table"""
        self.ui.info("Simple Table Example:")
        
        headers = ["Name", "Role", "Department", "Status"]
        rows = [
            ["John Doe", "Developer", "Engineering", "Active"],
            ["Jane Smith", "Designer", "UX Team", "Active"],
            ["Bob Johnson", "Manager", "Product", "On Leave"],
            ["Alice Brown", "QA Tester", "Engineering", "Active"],
            ["Charlie Wilson", "DevOps", "Infrastructure", "Inactive"]
        ]
        
        self.ui.table(headers, rows, title="Employee Directory")
        
    def _demo_advanced_table(self) -> None:
        """Demonstrate an advanced table"""
        self.ui.info("\nAdvanced Table Example:")
        
        # Create sample data
        data = [
            {"id": 1, "product": "Laptop", "price": 1299.99, "stock": 45, "rating": 4.8},
            {"id": 2, "product": "Smartphone", "price": 799.50, "stock": 120, "rating": 4.6},
            {"id": 3, "product": "Headphones", "price": 149.99, "stock": 30, "rating": 4.2},
            {"id": 4, "product": "Monitor", "price": 349.99, "stock": 15, "rating": 4.5},
            {"id": 5, "product": "Keyboard", "price": 59.99, "stock": 200, "rating": 4.0}
        ]
        
        # Define columns with custom formatting
        columns = [
            {"name": "id", "header": "ID", "width": 5},
            {"name": "product", "header": "Product Name", "width": 15},
            {"name": "price", "header": "Price ($)", "align": "right"},
            {"name": "stock", "header": "In Stock", "align": "center"},
            {"name": "rating", "header": "Rating", "align": "center"}
        ]
        
        # Display advanced table
        try:
            self.ui.advanced_table(data, columns, title="Product Inventory")
        except AttributeError:
            # Fallback if advanced_table not available
            headers = ["ID", "Product Name", "Price ($)", "In Stock", "Rating"]
            rows = [[str(item["id"]), item["product"], f"${item['price']:.2f}", 
                    str(item["stock"]), str(item["rating"])] for item in data]
            self.ui.table(headers, rows, title="Product Inventory")
            
    def _demo_paginated_table(self) -> None:
        """Demonstrate a paginated table"""
        self.ui.info("\nPaginated Table Example:")
        
        # Generate more sample data
        data = []
        for i in range(1, 31):
            data.append({
                "id": i,
                "name": f"Server-{i:03d}",
                "ip": f"192.168.1.{i}",
                "status": random.choice(["Online", "Offline", "Maintenance"]),
                "uptime": f"{random.randint(1, 365)} days",
                "load": round(random.random() * 100, 2)
            })
            
        # Display paginated table
        try:
            self.ui.paginated_table(
                ["ID", "Name", "IP Address", "Status", "Uptime", "Load %"],
                [[str(row["id"]), row["name"], row["ip"], row["status"], 
                  row["uptime"], str(row["load"])] for row in data],
                title="Server Status",
                page=1,
                page_size=5
            )
        except AttributeError:
            # Fallback if paginated_table not available
            headers = ["ID", "Name", "IP Address", "Status", "Uptime", "Load %"]
            rows = [[str(row["id"]), row["name"], row["ip"], row["status"], 
                    row["uptime"], str(row["load"])] for row in data[:5]]
            self.ui.table(headers, rows, title="Server Status (First 5 Items)")
            
    def _wait_for_input(self, message: str = "Press Enter to continue...") -> None:
        """Wait for user input"""
        self.ui.prompt(message)


class FormsCommand(BaseCommand):
    """Demonstrates interactive form capabilities"""

    @property
    def name(self) -> str:
        return "forms_demo"  # Internal name, not exposed directly

    def run(self, context: CommandContext) -> Any:
        """Execute the forms demo command"""
        self.ui.panel("Interactive Forms Demo", title="CHUI Framework", style="bold magenta")
        self.ui.info("This demo shows interactive form capabilities of the CHUI Framework.\n")
        
        # Simple form demo
        form_data = self._demo_simple_form()
        
        if form_data:
            self.ui.success("\nForm submitted successfully!")
            self.ui.info("Form data:")
            
            # Format and display the submitted data
            fields = []
            for key, value in form_data.items():
                fields.append(f"  {key}: {value}")
                
            self.ui.panel("\n".join(fields), title="Submitted Form Data", style="dim")
        else:
            self.ui.warning("\nForm submission cancelled or failed.")
        
        return True
        
    def _demo_simple_form(self) -> Dict[str, Any]:
        """Demonstrate a simple form"""
        self.ui.info("Please fill out the following form:")
        
        try:
            # Using specialized form methods if available
            from chui.ui.components.forms import (
                FormField, 
                FieldType,
                FormResult
            )
            
            # Create form fields
            fields = [
                FormField(
                    name="name",
                    label="Your Name",
                    field_type=FieldType.STRING,
                    required=True
                ),
                FormField(
                    name="email",
                    label="Email Address",
                    field_type=FieldType.STRING,
                    required=True,
                    pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                    pattern_description="Please enter a valid email address"
                ),
                FormField(
                    name="age",
                    label="Age",
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=18,
                    max_value=120
                ),
                FormField(
                    name="role",
                    label="Role",
                    field_type=FieldType.CHOICE,
                    choices=["Developer", "Designer", "Manager", "Other"],
                    required=True
                ),
                FormField(
                    name="subscribe",
                    label="Subscribe to newsletter?",
                    field_type=FieldType.BOOLEAN,
                    default=True
                )
            ]
            
            # Display form
            form_result = self.ui.input_form(fields, title="User Information")
            if form_result and form_result.valid:
                return form_result.values
                
            return {}
            
        except (ImportError, AttributeError):
            # Fallback to simple prompts if specialized form components not available
            return self._fallback_form()
            
    def _fallback_form(self) -> Dict[str, Any]:
        """Fallback form using simple prompts"""
        form_data = {}
        
        try:
            form_data["name"] = self.ui.prompt("Your Name")
            form_data["email"] = self.ui.prompt("Email Address")
            
            age = self.ui.prompt("Age (optional, must be 18-120)")
            if age:
                try:
                    age_val = int(age)
                    if 18 <= age_val <= 120:
                        form_data["age"] = age_val
                    else:
                        self.ui.warning("Age must be between 18 and 120. Skipping.")
                except ValueError:
                    self.ui.warning("Invalid age format. Skipping.")
            
            roles = ["Developer", "Designer", "Manager", "Other"]
            role_str = ", ".join([f"{i+1}: {r}" for i, r in enumerate(roles)])
            role_idx = self.ui.prompt(f"Role ({role_str})")
            try:
                idx = int(role_idx) - 1
                if 0 <= idx < len(roles):
                    form_data["role"] = roles[idx]
                else:
                    form_data["role"] = "Other"
            except ValueError:
                form_data["role"] = "Other"
                
            subscribe = self.ui.prompt("Subscribe to newsletter? (y/n)")
            form_data["subscribe"] = subscribe.lower() in ['y', 'yes', 'true']
            
            return form_data
            
        except Exception as e:
            self.ui.error(f"Error in form: {str(e)}")
            return {}


class PanelsCommand(BaseCommand):
    """Demonstrates panel display capabilities"""

    @property
    def name(self) -> str:
        return "panels_demo"  # Internal name, not exposed directly

    def run(self, context: CommandContext) -> Any:
        """Execute the panels demo command"""
        self.ui.panel("Panel Display Demo", title="CHUI Framework", style="bold cyan")
        self.ui.info("This demo shows various panel display capabilities of the CHUI Framework.\n")
        
        # Basic panel types
        self._demo_basic_panels()
        
        # Wait for user input before continuing
        self._wait_for_input("Press Enter to see advanced panels...")
        
        # Advanced panels demo
        self._demo_advanced_panels()
        
        self.ui.success("\nPanel demonstration completed!")
        return True
        
    def _demo_basic_panels(self) -> None:
        """Demonstrate basic panel types"""
        self.ui.info("Basic Panel Types:\n")
        
        # Standard Panel
        self.ui.panel(
            "This is a standard panel with default styling.",
            title="Standard Panel"
        )
        
        # Info Panel
        try:
            self.ui.info_panel(
                "This panel contains important information for the user.",
                title="Information"
            )
        except AttributeError:
            self.ui.panel(
                "This panel contains important information for the user.",
                title="Information"
            )
            
        # Success Panel
        try:
            self.ui.success_panel(
                "Operation completed successfully!",
                title="Success"
            )
        except AttributeError:
            self.ui.panel(
                "Operation completed successfully!",
                title="Success",
                style="green"
            )
            
        # Warning Panel
        try:
            self.ui.warning_panel(
                "This action may have unintended consequences.",
                title="Warning"
            )
        except AttributeError:
            self.ui.panel(
                "This action may have unintended consequences.",
                title="Warning",
                style="yellow"
            )
            
        # Error Panel
        try:
            self.ui.error_panel(
                "An error occurred while processing your request.",
                title="Error"
            )
        except AttributeError:
            self.ui.panel(
                "An error occurred while processing your request.",
                title="Error",
                style="red"
            )
            
    def _demo_advanced_panels(self) -> None:
        """Demonstrate advanced panel features"""
        self.ui.info("\nAdvanced Panel Features:\n")
        
        # Multi-section panel
        try:
            from chui.ui.displays.panels import create_section
            
            sections = [
                create_section(
                    title="System Information",
                    content="OS: Linux\nKernel: 5.15.0\nArchitecture: x86_64\nHostname: chui-demo"
                ),
                create_section(
                    title="Resource Usage",
                    content="CPU: 23%\nMemory: 4.2GB / 16GB\nDisk: 128GB / 512GB\nProcesses: 142"
                ),
                create_section(
                    title="Network Status",
                    content="Interface: eth0\nIP: 192.168.1.100\nStatus: Connected\nUptime: 14 days"
                )
            ]
            
            self.ui.panel_manager.display_multi_section_panel(
                sections,
                title="System Dashboard",
                panel_type="info"
            )
        except (ImportError, AttributeError):
            # Fallback for multi-section panel
            self.ui.panel(
                "System Information\n"
                "----------------\n"
                "OS: Linux\nKernel: 5.15.0\nArchitecture: x86_64\nHostname: chui-demo\n\n"
                "Resource Usage\n"
                "-------------\n"
                "CPU: 23%\nMemory: 4.2GB / 16GB\nDisk: 128GB / 512GB\nProcesses: 142\n\n"
                "Network Status\n"
                "--------------\n"
                "Interface: eth0\nIP: 192.168.1.100\nStatus: Connected\nUptime: 14 days",
                title="System Dashboard"
            )
            
        # Dictionary panel
        try:
            system_info = {
                "hostname": "chui-demo",
                "os": "Linux",
                "version": "5.15.0",
                "uptime": "14 days",
                "users": ["admin", "user1", "user2"],
                "network": {
                    "interface": "eth0",
                    "ip": "192.168.1.100",
                    "status": "Connected"
                }
            }
            
            self.ui.dict_panel(system_info, title="System Information")
        except AttributeError:
            pass  # Skip if dict_panel not available
            
        # Help panel with markdown
        try:
            help_text = """
            # CHUI Framework Help
            
            ## Command Syntax
            
            Commands in CHUI follow this syntax:
            ```
            command [options] [arguments]
            ```
            
            ## Common Options
            
            - `--help` - Show help for a command
            - `--debug` - Enable debug output
            - `--quiet` - Suppress non-error output
            
            ## Examples
            
            1. Show system status:
               ```
               system status
               ```
               
            2. Get help on a command:
               ```
               help command_name
               ```
            """
            
            self.ui.help_panel(help_text, title="Help Documentation")
        except AttributeError:
            # Fallback for help panel
            self.ui.panel(
                "CHUI Framework Help\n\n"
                "Command Syntax\n"
                "Commands in CHUI follow this syntax:\n"
                "command [options] [arguments]\n\n"
                "Common Options\n"
                "- --help - Show help for a command\n"
                "- --debug - Enable debug output\n"
                "- --quiet - Suppress non-error output\n\n"
                "Examples\n"
                "1. Show system status: system status\n"
                "2. Get help on a command: help command_name",
                title="Help Documentation"
            )
            
    def _wait_for_input(self, message: str = "Press Enter to continue...") -> None:
        """Wait for user input"""
        self.ui.prompt(message)


class PaginationCommand(BaseCommand):
    """Demonstrates pagination capabilities"""

    @property
    def name(self) -> str:
        return "pagination_demo"  # Internal name, not exposed directly

    def run(self, context: CommandContext) -> Any:
        """Execute the pagination demo command"""
        self.ui.panel("Pagination Demo", title="CHUI Framework", style="bold blue")
        self.ui.info("This demo shows pagination capabilities of the CHUI Framework.\n")
        
        # Generate sample data
        data = self._generate_sample_data(50)
        
        # Demonstrate pagination
        self._demo_pagination(data)
        
        self.ui.success("\nPagination demonstration completed!")
        return True
        
    def _generate_sample_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate sample data for pagination demo"""
        data = []
        status_options = ["Active", "Inactive", "Pending", "Archived"]
        
        for i in range(1, count + 1):
            # Generate a random date in the last 90 days
            created_date = datetime.now() - timedelta(days=random.randint(1, 90))
            
            data.append({
                "id": i,
                "name": f"Item-{i:03d}",
                "status": random.choice(status_options),
                "value": round(random.uniform(10, 1000), 2),
                "created": created_date.strftime("%Y-%m-%d"),
                "tags": random.sample(["tag1", "tag2", "tag3", "tag4", "tag5"], random.randint(1, 3))
            })
            
        return data
        
    def _demo_pagination(self, data: List[Dict[str, Any]]) -> None:
        """Demonstrate pagination with sample data"""
        self.ui.info("Paginated Data Display:")
        
        try:
            # Try to use the built-in pagination components
            from chui.ui.pagination import Paginator, Page
            
            page_size = 5
            paginator = Paginator(data, page_size)
            current_page = 1
            
            while True:
                # Clear previous display
                print("\n" * 2)
                
                # Get current page data
                page_obj = paginator.get_page(current_page)
                
                # Display the current page
                headers = ["ID", "Name", "Status", "Value", "Created", "Tags"]
                rows = []
                
                for item in page_obj.items:
                    rows.append([
                        str(item["id"]),
                        item["name"],
                        item["status"],
                        f"${item['value']:.2f}",
                        item["created"],
                        ", ".join(item["tags"])
                    ])
                
                self.ui.table(
                    headers, 
                    rows, 
                    title=f"Items (Page {current_page} of {page_obj.total_pages})"
                )
                
                # Display pagination info
                self.ui.info(f"\nShowing {len(page_obj.items)} of {page_obj.total_items} items")
                
                # Navigation options
                options = []
                if page_obj.has_previous:
                    options.append("p - Previous page")
                if page_obj.has_next:
                    options.append("n - Next page")
                options.append("q - Quit demo")
                
                self.ui.info("\nNavigation options:")
                for option in options:
                    self.ui.info(f"  {option}")
                
                # Get user input for navigation
                choice = self.ui.prompt("Enter option").lower()
                
                if choice == 'q':
                    break
                elif choice == 'n' and page_obj.has_next:
                    current_page += 1
                elif choice == 'p' and page_obj.has_previous:
                    current_page -= 1
                elif choice.isdigit():
                    page_num = int(choice)
                    if 1 <= page_num <= page_obj.total_pages:
                        current_page = page_num
                        
        except (ImportError, AttributeError):
            # Fallback if pagination components not available
            self._fallback_pagination(data)
            
    def _fallback_pagination(self, data: List[Dict[str, Any]]) -> None:
        """Fallback pagination demo"""
        page_size = 5
        total_pages = (len(data) + page_size - 1) // page_size
        current_page = 1
        
        while True:
            # Calculate slice indices
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(data))
            
            # Get current page data
            page_items = data[start_idx:end_idx]
            
            # Display the current page
            headers = ["ID", "Name", "Status", "Value", "Created", "Tags"]
            rows = []
            
            for item in page_items:
                rows.append([
                    str(item["id"]),
                    item["name"],
                    item["status"],
                    f"${item['value']:.2f}",
                    item["created"],
                    ", ".join(item["tags"])
                ])
            
            self.ui.table(
                headers, 
                rows, 
                title=f"Items (Page {current_page} of {total_pages})"
            )
            
            # Display pagination info
            self.ui.info(f"\nShowing {len(page_items)} of {len(data)} items")
            
            # Navigation options
            options = []
            if current_page > 1:
                options.append("p - Previous page")
            if current_page < total_pages:
                options.append("n - Next page")
            options.append("q - Quit demo")
            
            self.ui.info("\nNavigation options:")
            for option in options:
                self.ui.info(f"  {option}")
            
            # Get user input for navigation
            choice = self.ui.prompt("Enter option").lower()
            
            if choice == 'q':
                break
            elif choice == 'n' and current_page < total_pages:
                current_page += 1
            elif choice == 'p' and current_page > 1:
                current_page -= 1
            elif choice.isdigit():
                page_num = int(choice)
                if 1 <= page_num <= total_pages:
                    current_page = page_num


class ProgressCommand(BaseCommand):
    """Demonstrates progress indicators"""

    @property
    def name(self) -> str:
        return "progress_demo"  # Internal name, not exposed directly

    def run(self, context: CommandContext) -> Any:
        """Execute the progress indicators demo command"""
        self.ui.panel("Progress Indicators Demo", title="CHUI Framework", style="bold green")
        self.ui.info("This demo shows progress indicators and animation capabilities.\n")
        
        # Simple progress demo
        self._demo_simple_progress()
        
        # Wait for user input before continuing
        self._wait_for_input("Press Enter to see a task progress simulation...")
        
        # Task progress demo
        self._demo_task_progress()
        
        self.ui.success("\nProgress indicators demonstration completed!")
        return True
        
    def _demo_simple_progress(self) -> None:
        """Demonstrate simple progress indicators"""
        self.ui.info("Simple Progress Indicator:")
        
        try:
            # Try to use rich progress bar if available
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.ui.console
            ) as progress:
                task = progress.add_task("[green]Processing...", total=100)
                
                for i in range(101):
                    progress.update(task, completed=i)
                    time.sleep(0.05)
        
        except (ImportError, AttributeError):
            # Fallback for simple progress
            self.ui.info("Processing: ", end="")
            for i in range(20):
                print("█", end="", flush=True)
                time.sleep(0.2)
            print(" Done!")
            
    def _demo_task_progress(self) -> None:
        """Demonstrate task progress with multiple steps"""
        self.ui.info("\nSimulating a complex task with multiple steps:")
        
        # Define tasks
        tasks = [
            {"name": "Connecting to server", "duration": 2},
            {"name": "Authenticating", "duration": 1},
            {"name": "Loading configuration", "duration": 1.5},
            {"name": "Processing data", "duration": 3},
            {"name": "Generating report", "duration": 2},
            {"name": "Cleaning up", "duration": 1}
        ]
        
        try:
            # Try to use rich progress bar for tasks
            from rich.progress import Progress, SpinnerColumn, TextColumn
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]{task.description}"),
                TextColumn("[cyan]{task.fields[status]}"),
                console=self.ui.console
            ) as progress:
                # Add all tasks
                task_ids = []
                for task in tasks:
                    task_id = progress.add_task(task["name"], status="Pending...", total=1)
                    task_ids.append(task_id)
                
                # Execute tasks
                for i, (task, task_id) in enumerate(zip(tasks, task_ids)):
                    # Update current task
                    progress.update(task_id, status="In progress...")
                    
                    # Simulate work
                    time.sleep(task["duration"])
                    
                    # Mark task as completed
                    progress.update(task_id, status="[bold green]Completed[/bold green]", completed=1)
        
        except (ImportError, AttributeError):
            # Fallback for task progress
            total_tasks = len(tasks)
            for i, task in enumerate(tasks, 1):
                self.ui.info(f"[{i}/{total_tasks}] {task['name']}...")
                time.sleep(task["duration"])
                print("Done!")
                
    def _wait_for_input(self, message: str = "Press Enter to continue...") -> None:
        """Wait for user input"""
        self.ui.prompt(message)


class ColorsCommand(BaseCommand):
    """Demonstrates color capabilities"""

    @property
    def name(self) -> str:
        return "colors_demo"  # Internal name, not exposed directly

    def run(self, context: CommandContext) -> Any:
        """Execute the colors demo command"""
        self.ui.panel("Color Capabilities Demo", title="CHUI Framework", style="bold magenta")
        self.ui.info("This demo shows color and styling capabilities of the CHUI Framework.\n")
        
        # Basic text styles
        self._demo_text_styles()
        
        # Wait for user input before continuing
        self._wait_for_input("Press Enter to see colored panels...")
        
        # Colored panels demo
        self._demo_colored_panels()
        
        # Wait for user input before continuing
        self._wait_for_input("Press Enter to see styled tables...")
        
        # Styled tables demo
        self._demo_styled_tables()
        
        self.ui.success("\nColor capabilities demonstration completed!")
        return True
        
    def _demo_text_styles(self) -> None:
        """Demonstrate text styling capabilities"""
        self.ui.info("Basic Text Styling:")
        
        # Output text with different styles
        self.ui.console.print("[bold]Bold text[/bold]")
        self.ui.console.print("[italic]Italic text[/italic]")
        self.ui.console.print("[underline]Underlined text[/underline]")
        self.ui.console.print("[dim]Dimmed text[/dim]")
        self.ui.console.print("[strike]Strikethrough text[/strike]")
        
        self.ui.info("\nText Colors:")
        
        # Output text with different colors
        self.ui.console.print("[red]Red text[/red]")
        self.ui.console.print("[green]Green text[/green]")
        self.ui.console.print("[blue]Blue text[/blue]")
        self.ui.console.print("[yellow]Yellow text[/yellow]")
        self.ui.console.print("[magenta]Magenta text[/magenta]")
        self.ui.console.print("[cyan]Cyan text[/cyan]")
        
        self.ui.info("\nCombined Styles:")
        
        # Output text with combined styles
        self.ui.console.print("[bold red]Bold red text[/bold red]")
        self.ui.console.print("[italic blue]Italic blue text[/italic blue]")
        self.ui.console.print("[bold yellow on black]Yellow text on black background[/bold yellow on black]")
        self.ui.console.print("[reverse green]Reversed green (green background, black text)[/reverse green]")
        
    def _demo_colored_panels(self) -> None:
        """Demonstrate colored panels"""
        self.ui.info("\nColored Panels:")
        
        # Output panels with different styles
        self.ui.panel("This is a panel with default styling", title="Default Panel")
        self.ui.panel("This is a panel with blue styling", title="Blue Panel", style="blue")
        self.ui.panel("This is a panel with bold red styling", title="Red Panel", style="bold red")
        self.ui.panel("This is a panel with dim cyan styling", title="Cyan Panel", style="dim cyan")
        self.ui.panel("This is a panel with yellow styling and border", title="Yellow Panel", style="yellow")
        
    def _demo_styled_tables(self) -> None:
        """Demonstrate styled tables"""
        self.ui.info("\nStyled Tables:")
        
        # Create sample data
        headers = ["ID", "Product", "Category", "Price", "Status"]
        rows = [
            ["1", "Laptop", "Electronics", "$1,299.99", "In Stock"],
            ["2", "Desk Chair", "Furniture", "$249.99", "Low Stock"],
            ["3", "Coffee Maker", "Appliances", "$89.99", "Out of Stock"],
            ["4", "Wireless Mouse", "Electronics", "$29.99", "In Stock"],
            ["5", "Bookshelf", "Furniture", "$199.99", "In Stock"]
        ]
        
        # Create styled table
        from rich.table import Table
        from rich.style import Style
        
        # Create table with styling
        table = Table(title="Product Inventory", show_header=True, header_style="bold")
        
        # Add columns with specific styles
        table.add_column("ID", style="dim")
        table.add_column("Product")
        table.add_column("Category", style="cyan")
        table.add_column("Price", style="green", justify="right")
        table.add_column("Status", style="bold")
        
        # Add rows with conditional styling
        for row in rows:
            if row[4] == "In Stock":
                status_style = "green"
            elif row[4] == "Low Stock":
                status_style = "yellow"
            else:
                status_style = "red"
                
            # Override the status with styled version
            row_with_style = row.copy()
            row_with_style[4] = f"[{status_style}]{row[4]}[/{status_style}]"
            
            table.add_row(*row_with_style)
            
        # Display the table
        self.ui.console.print(table)
        
    def _wait_for_input(self, message: str = "Press Enter to continue...") -> None:
        """Wait for user input"""
        self.ui.prompt(message)