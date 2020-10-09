import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory

from .timetable_parser import TimetableParser, CalendarNotFoundError, TimetableNotFoundError, DirectoryNotFoundError
from .google_calendar import GoogleCalendarUploader, CalendarQuotaError

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.timetable_entry = tk.Entry(self)
        self.timetable_button = tk.Button(self)
        self.timetable_button["text"] = "Choose timetable file"
        self.timetable_button["command"] = self.choose_timetable_file

        self.calendar_entry = tk.Entry(self)
        self.calendar_button = tk.Button(self)
        self.calendar_button["text"] = "Choose calendar file"
        self.calendar_button["command"] = self.choose_calendar_file

        self.output_entry = tk.Entry(self)
        self.output_button = tk.Button(self)
        self.output_button["text"] = "Choose output directory"
        self.output_button["command"] = self.choose_output_folder

        self.timetable_entry.grid(row=0, column=0)
        self.timetable_button.grid(row=0, column=1)
        self.calendar_entry.grid(row=1, column=0)
        self.calendar_button.grid(row=1, column=1)

        # self.upload_button = tk.Button(self, text="Upload", command=self.upload)
        # self.upload_button.grid(row=2, column=0)

        self.save_button = tk.Button(self)
        self.save_button["text"] = "Save"
        self.save_button["command"] = self.save

        self.output_entry.grid(row=2, column=0)
        self.output_button.grid(row=2, column=1)
        self.save_button.grid(row=3, column=0)

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.grid(row=3, column=1)

    def save(self):
        calendar = self.calendar_entry.get()
        timetable = self.timetable_entry.get()
        directory = self.output_entry.get()
        try:
            parser = TimetableParser(timetable, calendar)
        except CalendarNotFoundError:
            self.warning_dialog("Could not find calendar file")
            return
        except TimetableNotFoundError:
            self.warning_dialog("Could not find timetable file")
            return
        except Exception as e:
            self.warning_dialog(str(e))
            return
        try:
            parser.create_calendars()
            parser.save_calendars(directory)
        except Exception as e:
            self.warning_dialog(str(e))
        

    def choose_output_folder(self):
        self.output_entry.delete(0, "end")
        directory = askdirectory()
        self.output_entry.insert(0, directory)

    def choose_timetable_file(self):
        self.timetable_entry.delete(0, "end")
        filename = askopenfilename()
        self.timetable_entry.insert(0, filename)
    
    def choose_calendar_file(self):
        self.calendar_entry.delete(0, "end")
        filename = askopenfilename()
        self.calendar_entry.insert(0, filename)

    def upload(self):
        calendar = self.calendar_entry.get()
        timetable = self.timetable_entry.get()
        try:
            parser = TimetableParser(timetable, calendar)
        except CalendarNotFoundError:
            self.warning_dialog("Could not find calendar file")
            return
        except TimetableNotFoundError:
            self.warning_dialog("Could not find timetable file")
            return
        except Exception as e:
            self.warning_dialog(str(e))
            return
        try:
            parser.create_calendars()
        except Exception as e:
            self.warning_dialog(str(e))
        
        self.upload_window(parser.calendars)
    
    def upload_window(self, calendars):
        up = GoogleCalendarUploader()
        print("Creating window")
        self.window = tk.Toplevel(self.master)
        self.master.withdraw()
        self.master.update()
        print("Created window")
        message = tk.StringVar(self.window)
        label = tk.Label(self.window, textvariable=message)
        label.grid(row=0)
        for name, cal in calendars.items():
            print(f"Uploading calendar for {name}")
            message.set(f"Uploading calendar for {name}")
            self.window.update()
            try:
                up.upload_calendar_data(cal)
            except CalendarQuotaError:
                message.set("You have reached the calendar upload quota for google. Please wait a few hours and try again")
                break
            except:
                message.set("Unknown error")
                break
        else:
            message.set("Finished uploading calendars")
        button = tk.Button(self.window, command=self.reopen, text="Ok")
        button.grid(row=1)
    
    def reopen(self):
        self.window.destroy()
        self.master.deiconify()

    def warning_dialog(self, message):
        self.master.withdraw()
        messagebox.showerror(title="Error", message=message)
        self.master.deiconify()


def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()