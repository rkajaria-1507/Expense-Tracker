class CommandParser:
    def __init__(self):
        self.commands = {}
        self.filter_commands = []
        self.report_commands = []
        
    def register_command(self, command, handler, privilege_required=None):
        self.commands[command] = {'handler': handler, 'privilege': privilege_required}
        
    def register_filter_command(self, command):
        self.filter_commands.append(command)
        
    def register_report_command(self, command):
        self.report_commands.append(command)
        
    def parse_command(self, command_line, current_user, current_privileges):
        if not command_line:
            return None, []
            
        # Split the command line into tokens
        tokens = command_line.split()
        command = tokens[0].lower()
        args = tokens[1:]
        
        # Special handling for filter commands
        if command in self.filter_commands:
            # Process complex filter logic
            return self._parse_filter_command(command, args)
            
        # Return the command and its arguments
        return command, args
        
    def _parse_filter_command(self, command, args):
        """Parse complex filter commands with special syntax"""
        filter_types = {
            'amount': [],
            'date': [],
            'category': [],
            'tag': [],
            'payment_method': [],
            'month': []
        }
        
        # Process each filter argument
        i = 0
        while i < len(args):
            if args[i] in filter_types:
                current_filter = args[i]
                i += 1
                
                # Process operators and values for this filter
                while i < len(args) and args[i] not in filter_types:
                    if i + 1 < len(args) and args[i] in ['=', '>', '<', '>=', '<=', '!=']:
                        op = args[i]
                        value = args[i+1]
                        filter_types[current_filter].append((op, value))
                        i += 2
                    else:
                        # Invalid filter format, skip to next filter type
                        break
            else:
                # Skip unknown filter types
                i += 1
        
        return command, filter_types
        
    def execute_command(self, command, args, current_user, current_privileges):
        """Execute a command with the given arguments"""
        if command not in self.commands:
            print(f"Unknown command: {command}")
            return False
            
        cmd_info = self.commands[command]
        
        # Check privileges
        if cmd_info['privilege'] and cmd_info['privilege'] != current_privileges:
            print(f"Error: You don't have permission to use the '{command}' command.")
            return False
            
        # Execute the command handler
        return cmd_info['handler'](args)