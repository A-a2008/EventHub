from django.shortcuts import render, redirect
from django.apps import apps
from django.db.models import F
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import os
import zipfile
from pydub import AudioSegment
import logging
from datetime import datetime
import pytz

Event = apps.get_model('main', "Event")
SubEvents = apps.get_model('main', "SubEvents")
Files = apps.get_model('main', "Files")

timezone_asia = pytz.timezone("Asia/Kolkata")
current_time = datetime.now(timezone_asia).strftime("%I-%M-%S %p")
logging.basicConfig(level=logging.INFO, filename=f"./logs/log {timezone.now().date().strftime('%d-%m-%Y')} {current_time}.log", filemode="w")

# Create your views here.

def home(request):
    return render(request, "index.html")


def elements(request):
    return render(request, "elements.html")


def base(request):
    return render(request, "base.html")


def testing(request):
    return render(request, "base_testing.html")


@login_required
def events_display(request):
    all_events = Event.objects.filter(models.Q(creators=request.user) | models.Q(users=request.user)).distinct()
    for event in all_events:
        print(event.name, event.id)

    data = {
        'events': all_events,
    }

    return render(request, "main/events_display.html", data)

@login_required
def subevents_display(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user in event.users.all() or request.user in event.creators.all():
        subevents = SubEvents.objects.filter(event=event)

        no_digits_event_id = len(str(event_id))
        subevents_unsorted = []
        for subevent in subevents:
            subevents_unsorted.append((int(str(subevent.order)[no_digits_event_id+2:]), subevent.name, subevent.id))

        subevents_sorted = []
        for _, name, id in sorted(subevents_unsorted):
            subevents_sorted.append((name, id))

        creator = False
        if request.user in event.creators.all():
            creator = True

        data = {
            'event': event,
            'subevents_display': subevents_sorted,
            'subevents_display_subevents_zip': zip(subevents_sorted, subevents),
            'event_id': event.id,
            'creator': creator,
        }

        return render(request, "main/subevents_display.html", data)
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': "Event doesn't exist",
            'error_detail': 'This event has either been deleted or you have been removed from this event.'
        }

        return render(request, "errors/error.html", data)

@login_required
def new_event_page(request):
    return render(request, "main/new_event.html")

@login_required
def new_event_process(request):
    name = request.POST["event_name"]
    description = request.POST["event_description"]
    creator = request.user

    event = Event.objects.create(
        name=name,
        description=description,
    )

    event.creators.add(creator)

    data = {
        "event_id": event.id
    }

    return render(request, "main/new_subevents.html", data)

@login_required
def new_subevent_page(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user in event.creators.all():
        data = {
            'event_id': event.id,
        }

        return render(request, "main/new_subevents.html", data)
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Subevent creation denied.',
            'error_detail': 'You are not authorized to create a subevent in this event. Ask the event head to create it for you.'
        }

        return render(request, "errors/error.html", data)

@login_required
def new_subevent_process(request, event_id):
    name = request.POST['subevent_name']
    user = request.user
    event = Event.objects.get(id=event_id)
    if request.user in event.creators.all():
        subevents = SubEvents.objects.filter(event=event)
        subevent_order = [0]
        no_digits_event_id = len(str(event_id))
        for subevent in subevents:
            id = int(str(subevent.order)[no_digits_event_id+2:])
            subevent_order.append(id)

        subevent_id = int(f"{event_id}00{max(subevent_order)+1}")

        subevent = SubEvents.objects.create(
            event=event,
            order=subevent_id,
            name=name
        )

        subevent.users.add(user)

        return redirect(f"/subevent/new/{event.id}")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Subevent creation denied.',
            'error_detail': 'You are not authorized to create a subevent in this event. Ask the event head to create it for you.'
        }

        return render(request, "errors/error.html", data)

@login_required
def edit_subevent_order_page(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user in event.creators.all():
        subevents = SubEvents.objects.filter(event=event)

        all_subevents_unsorted = []
        for subevent in subevents:
            all_subevents_unsorted.append((subevent.order, subevent.name, subevent.id))

        all_subevents_sorted = []
        for order, name, id in sorted(all_subevents_unsorted):
            all_subevents_sorted.append((str(order)[len(str(event_id))+2:], name, id))

        data = {
            'event_id': event_id,
            'event_name': event.name,
            'subevents_data': all_subevents_sorted,
        }

        return render(request, "main/edit_subevent_order.html", data)
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Subevent Order edit access denied.',
            'error_detail': 'You are not authorized to edit the order of subevents in this event. Ask the event head to edit it for you.'
        }

        return render(request, "errors/error.html", data)
    
@login_required
def edit_subevent_order_process(request, event_id):
    change_to = []
    subevents_no = 0
    for name, value in zip(request.POST.keys(), request.POST.values()):
        if "change_" in name:
            change_to.append(value)
            subevents_no += 1
    
    if len(set(change_to)) != subevents_no:
        data = {
            'title': "Error",
            'subtitle': f"Could not edit the order of subevents",
            'error_detail': "More than one subevent has the same Serial Number. The order has not been changed from the previous one and still can be changed."
        }
        return render(request, "errors/error.html", data)

    all_inputs = {}
    for name, value in zip(request.POST.keys(), request.POST.values()):
        if "change_" in name:
            subevent_id = name[7:]
            all_inputs[subevent_id] = value
            current_subevent = SubEvents.objects.get(id=subevent_id)
            current_subevent.order = f"{event_id}00{value}"
            current_subevent.save()

            files = Files.objects.filter(sub_events_id=subevent_id)
            for current_file in files:
                old_file_name = current_file.file.name[len("\\file_uploads\\"):]
                old_file_name = old_file_name[old_file_name.index(","):]
                new_file_name = f"[{value}" + old_file_name
                new_file_path = settings.MEDIA_ROOT + "\\file_uploads\\" + new_file_name
                old_file_path = settings.MEDIA_ROOT + current_file.file.name
                current_file.file.name = "\\file_uploads\\" + new_file_name
                os.rename(old_file_path, new_file_path)
                current_file.save()
                print(old_file_path)
                print(new_file_path)
                print()

    print(all_inputs)
    return redirect(f"/subevents/{event_id}")

@login_required
def edit_subevent_files_page(request, subevent_id):
    subevent = SubEvents.objects.get(id=subevent_id)
    event = Event.objects.get(id=subevent.event_id)
    creator = False
    if request.user in event.creators.all():
        creator = True
    if request.user in subevent.users.all():
        files = Files.objects.filter(sub_events=subevent)

        all_files_unsorted = []
        for file in files:
            all_files_unsorted.append((file.order, str(file.file)[14:]))

        all_files_sorted = []
        for file_order, name in sorted(all_files_unsorted):
            all_files_sorted.append((file_order, name))

        show_edit_order = True
        if len(all_files_sorted) == 1:
            show_edit_order = False

        data = {
            'subevent': subevent,
            'files': all_files_sorted,
            'show_edit_order': show_edit_order,
            'creator': creator,
            'event': event,
        }

        return render(request, "main/edit_subevent_files.html", data)
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Editing this subevent is denied.',
            'error_detail': 'You are not authorized to edit this subevent. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)

@login_required
def edit_subevent_name(request, subevent_id):
    subevent = SubEvents.objects.get(id=subevent_id)
    if request.user in subevent.users.all():
        name = request.POST["subevent_name"]
        logging.info(f"Subevent name changed from {subevent.name} -> {name}")
        subevent.name = name
        subevent.save()

        return redirect(f"/subevent/edit_files/{subevent_id}/")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Editing this subevent is denied.',
            'error_detail': 'You are not authorized to edit this subevent. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)
    
@login_required
def edit_event_name(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user in event.creators.all():
        name = request.POST["event_name"]
        logging.info(f"Subevent name changed from {event.name} -> {name}")
        event.name = name
        event.save()

        return redirect(f"/subevents/{event_id}/")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': "Editing this event's name is denied.",
            'error_detail': "You are not authorized to edit this event's name. Ask the event head to do it for you."
        }

        return render(request, "errors/error.html", data)

@login_required
def edit_subevent_files_process(request, subevent_id):
    subevent = SubEvents.objects.get(id=subevent_id)
    if request.user in subevent.users.all():
        subevent_id = str(subevent.order).split("00")[-1]
        
        files = Files.objects.filter(sub_events=subevent)
        files_order = [0]
        no_digits_subevent_id = len(str(subevent_id))
        for file in files:
            file_id = int(str(file.order)[no_digits_subevent_id+2:])
            files_order.append(file_id)
        
        current_file_id = int(f"{subevent_id}00{max(files_order)+1}")

        file = Files.objects.create(
            sub_events=subevent,
            file=request.FILES["file"],
            order=current_file_id
        )

        initial_file_path = file.file.path
        user_file_name = initial_file_path.split("\\")[-1] # Check this line when deploying!!!!
        print(user_file_name)
        file.file.name = f"\\file_uploads\\[{subevent_id}, {max(files_order)+1}] {user_file_name}" # Check this line when deploying!!!!
        new_file_path = settings.MEDIA_ROOT + file.file.name
        os.rename(initial_file_path, new_file_path)
        file.save()

        return redirect(f"/subevent/edit_files/{subevent.id}/")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Editing this subevent is denied.',
            'error_detail': 'You are not authorized to edit this subevent. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)

@login_required
def edit_subevent_fileorder_page(request, subevent_id):
    subevent = SubEvents.objects.get(id=subevent_id)
    if request.user in subevent.users.all():
        subevent_id = str(subevent.order).split("00")[-1]
        files = Files.objects.filter(sub_events=subevent)

        all_files_unsorted = []
        for file in files:
            all_files_unsorted.append((file.order, str(file.file)[14:], file.id))

        all_files_sorted = []
        for order, name, id in sorted(all_files_unsorted):
            all_files_sorted.append((str(order)[len(str(subevent_id))+2:], name, id))

        data = {
            'subevent_id': subevent.id,
            'subevent_name': subevent.name,
            'files_data': all_files_sorted,
        }

        return render(request, "main/edit_subevent_filesorder.html", data)
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Editing this subevent is denied.',
            'error_detail': 'You are not authorized to edit this subevent. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)

@login_required
def edit_subevent_fileorder_process(request, subevent_id):
    change_to = []
    files_no = 0
    for name, value in zip(request.POST.keys(), request.POST.values()):
        if "change_" in name:
            change_to.append(value)
            files_no += 1
    
    if len(set(change_to)) != files_no:
        data = {
            'title': "Error",
            'subtitle': f"Could not edit the order of the files",
            'error_detail': "More than one file has the same Serial Number. The order has not been changed from the previous one and still can be changed."
        }
        return render(request, "errors/error.html", data)
    
    subevent = SubEvents.objects.get(id=subevent_id)
    if request.user in subevent.users.all():
        prefix = str(subevent.order).split("00")[-1]
        
        all_inputs = {}
        for name, value in zip(request.POST.keys(), request.POST.values()):
            if "change_" in name:
                all_inputs[name[7:]] = value
                current_file = Files.objects.get(id=name[7:])
                current_file.order = f"{prefix}00{value}"
                old_file_name = current_file.file.name[len("\\file_uploads\\"):]
                old_file_name = old_file_name[old_file_name.index("]")+1:]
                new_file_name = f"[{prefix}, {value}]" + old_file_name
                new_file_path = settings.MEDIA_ROOT + "\\file_uploads\\" + new_file_name
                old_file_path = settings.MEDIA_ROOT + current_file.file.name
                current_file.file.name = "\\file_uploads\\" + new_file_name
                os.rename(old_file_path, new_file_path)
                current_file.save()

        print(all_inputs)
        return redirect(f"/subevent/edit_files/{subevent_id}")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Editing this subevent is denied.',
            'error_detail': 'You are not authorized to edit this subevent. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)

@login_required
def delete_subevent_file_confirm(request, subevent_id, file_order):
    subevent = SubEvents.objects.get(id=subevent_id)
    file = Files.objects.get(order=file_order)
    file_name = file.file.name[len("\\file_uploads\\"):]

    data = {
        'subevent': subevent,
        'file_name': file_name,
        'order': file_order,
    }

    return render(request, "main/delete_subevent_file_confirm_page.html", data)

@login_required
def delete_subevent_file(request, subevent_id, file_order):
    file = Files.objects.get(order=file_order)
    file_path = settings.MEDIA_ROOT + file.file.name
    logging.info(f"File Deleted: {request.user.email} deleted {file.file.name}")
    os.remove(file_path)
    file.delete()

    subevent = SubEvents.objects.get(id=subevent_id)
    subevent_rank = str(subevent.order).split("00")[-1]
    if request.user in subevent.users.all():
        file_rank = int(str(file_order).split("00")[-1])
        files = Files.objects.filter(sub_events_id=subevent_id)
        for file in files:
            current_file_rank = int(str(file.order).split("00")[-1])
            if current_file_rank > file_rank:
                current_file_rank -= 1
                file.order = f"{subevent_rank}00{current_file_rank}"
                old_file_name = file.file.name[len("\\file_uploads\\"):]
                old_file_name = old_file_name[old_file_name.index("]")+1:]
                new_file_name = f"[{subevent_rank}, {current_file_rank}]" + old_file_name
                new_file_path = settings.MEDIA_ROOT + "\\file_uploads\\" + new_file_name
                old_file_path = settings.MEDIA_ROOT + file.file.name
                file.file.name = "\\file_uploads\\" + new_file_name
                os.rename(old_file_path, new_file_path)
                file.save()

        return redirect(f"/subevent/edit_files/{subevent_id}")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Deleting this file is denied.',
            'error_detail': 'You are not authorized to delete a file. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)

@login_required
def delete_subevent_confirm(request, subevent_id):
    subevent = SubEvents.objects.get(id=subevent_id)

    data = {
        'subevent': subevent,
    }

    return render(request, "main/delete_subevent_confirm_page.html", data)

@login_required
def delete_subevent(request, subevent_id):
    subevent = SubEvents.objects.get(id=subevent_id)
    event_id = str(subevent.order).split("00")[0]
    event = Event.objects.get(id=event_id)
    logging.info(f"Subevent Deleted: {request.user.email} deleted {subevent.name}; Event: {event.name}")
    if request.user in event.creators.all():
        files = Files.objects.filter(sub_events_id=subevent_id)

        for file in files:
            file_path = settings.MEDIA_ROOT + file.file.name
            os.remove(file_path)
            file.delete()

        event_id = subevent.event_id
        subevent_rank = int(str(subevent.order).split("00")[-1])
        subevent.delete()

        subevents = SubEvents.objects.filter(event_id=event_id)
        for subevent in subevents:
            current_subevent_rank = int(str(subevent.order).split("00")[-1])
            if current_subevent_rank > subevent_rank:
                current_subevent_rank -= 1
                subevent.order = f"{event_id}00{current_subevent_rank}"
                subevent.save()

        return redirect(f"/subevents/{subevent.event_id}/")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Deleting this subevent is denied.',
            'error_detail': 'You are not authorized to delete this subevent. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)

@login_required
def delete_event_confirm(request, event_id):
    event = Event.objects.get(id=event_id)

    data = {
        'event': event,
    }

    return render(request, "main/delete_event_confirm_page.html", data)

@login_required
def delete_event(request, event_id):
    event = Event.objects.get(id=event_id)
    logging.info(f"Event Deleted: {request.user.email} deleted {event.name}")
    if request.user in event.creators.all():
        subevents = SubEvents.objects.filter(event=event)

        for subevent in subevents:
            files = Files.objects.filter(sub_events=subevent)

            for file in files:
                file_path = settings.MEDIA_ROOT + file.file.name
                os.remove(file_path)
                file.delete()

            subevent.delete()

        event.delete()

        return redirect("/myevents/")
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Deleting this event is denied.',
            'error_detail': 'You are not authorized to delete this event. Ask the event head to grant the access.'
        }

        return render(request, "errors/error.html", data)
    
@login_required
def share_event(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user in event.creators.all():
        if request.method == "POST":
            email = request.POST["email"]
            creator = request.POST.get("creator")
            if creator == "on":
                creator = True
            else:
                creator = False
            subevents = []
            for key, value in zip(request.POST.keys(), request.POST.values()):
                if "subevent_" in key:
                    subevent = SubEvents.objects.get(id=value)
                    subevents.append(subevent)

            shared_to = User.objects.filter(
                models.Q(email=email),
            ).first()

            print(subevents)

            if shared_to:
                if creator:
                    if shared_to not in event.creators.all():
                        event.creators.add(shared_to)
                        all_subevents = SubEvents.objects.filter(event=event)
                        for subevent in all_subevents:
                            subevent.users.add(shared_to)
                    else:
                        data = {
                            'title': f"{shared_to.first_name} already a admin",
                            'error_detail': f"{shared_to.first_name} is already an admin in this event.",
                        }

                        return render(request, "errors/error.html", data)
                else:
                    event.creators.remove(shared_to)
                    if shared_to not in event.users.all():
                        event.users.add(shared_to)
                        for subevent in subevents:
                            subevent.users.add(shared_to)
                    else:
                        all_subevents = SubEvents.objects.filter(event=event)
                        for subevent in all_subevents:
                            subevent.users.remove(shared_to)
                        for subevent in subevents:
                            subevent.users.add(shared_to)
                    
                data = {
                    'event': event,
                    'user_to': shared_to,
                }

                return render(request, "main/event_shared.html", data)
            else:
                data = {
                    'title': "User doesn't exist",
                    'error_detail': f'To share this event with <b>"{email}"</b>, please make sure they have an account in this website.'
                }

                return render(request, "errors/error.html", data)
            
        else:
            subevents = SubEvents.objects.filter(event=event)
            data = {
                'event': event,
                'subevents': subevents,
            }
            return render(request, "main/share_event.html", data)
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Sharing this event is denied.',
            'error_detail': 'You are not authorized to share this event. Ask the event head to share it for you.'
        }

        return render(request, "errors/error.html", data)
    
@login_required
def manage_event(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user in event.creators.all():
        if request.method == "POST":
            creators = []
            users = []
            for key, value in zip(request.POST.keys(), request.POST.values()):
                if "creator_" in key:
                    creators.append(int(value))
                elif "user_" in key:
                    users.append(int(value))

            print(creators, users)

            for creator in creators:
                user = User.objects.get(id=creator)
                all_subevents = SubEvents.objects.filter(event=event)
                for subevent in all_subevents:
                    subevent.users.remove(user)
                event.creators.remove(user)

            for person in users:
                user = User.objects.get(id=person)
                all_subevents = SubEvents.objects.filter(event=event)
                for subevent in all_subevents:
                    subevent.users.remove(user)
                event.users.remove(user)

            data = {
                'event': event,
            }

            return render(request, "main/users_removed.html", data)
        else:
            data = {
                'event': event
            }

            return render(request, "main/manage_event.html", data)
    else:
        data = {
            'title': 'Authorization Error',
            'subtitle': 'Managing this event is denied.',
            'error_detail': 'You are not authorized to manage this event. Ask the event head to grant you the access.'
        }

        return render(request, "errors/error.html", data)

@login_required
def dowload_files(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.user in event.creators.all():
        subevents = SubEvents.objects.filter(event=event).order_by('order')
        file_paths = {}

        for subevent in subevents:
            files = Files.objects.filter(sub_events=subevent).order_by('order')
            subevent_files = []
            for file in files:
                subevent_files.append(file.file.name)
            file_paths[subevent.name] = subevent_files
        
        single_file = request.POST.get('duration_check')
        duration = request.POST.get('duration')
        if single_file == 'on':
            single_file = True
            if duration == '':
                duration = 0
        else:
            single_file = False

        download_zip = ''

        if single_file:
            download_zip = single_file_edit(file_paths, event.name, duration)
        else:
            download_zip = audio_files_edit(file_paths, event.name)

        data = {
            'event': event,
            'zip_file': download_zip,
        }

        return render(request, "main/download_files.html", data)

def audio_files_edit(file_paths, event_name):
    current_date = timezone.now().date().strftime('%d-%m-%Y')

    zip_file_name = f'{event_name}-{current_date}.zip'

    zip_file_path = os.path.join(settings.MEDIA_ROOT, zip_file_name)
    zip_file_url = os.path.join(settings.MEDIA_URL, zip_file_name)

    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        for subevent_name in file_paths:
            for file_path in file_paths[subevent_name]:
                file_path = file_path.lstrip("\\")
                file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                file_name = os.path.basename(file_path)
                zip_file.write(file_path, arcname=os.path.join(subevent_name, file_name))
                if file_path.endswith('.mp3'):
                    zip_file.write(file_path, arcname=os.path.join("All Music Files", file_name))
                    
    return zip_file_url

def single_file_edit(file_paths, event_name, gap_duration):
    current_date = timezone.now().date().strftime('%d-%m-%Y')

    zip_file_name = f'{event_name}-{current_date} Single File.zip'

    zip_file_path = os.path.join(settings.MEDIA_ROOT, zip_file_name)
    zip_file_url = os.path.join(settings.MEDIA_URL, zip_file_name)

    combined_audio = AudioSegment.empty()

    for subevent_name in file_paths:
        for file_path in file_paths[subevent_name]:
            if file_path.endswith('.mp3'):
                file_path = file_path.lstrip("\\")
                file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                audio = AudioSegment.from_mp3(file_path)
                combined_audio += audio + AudioSegment.silent(duration=float(gap_duration) * 1000)
    
    output_file_name = f"{event_name}-{timezone.now().date().strftime('%d-%m-%Y')}.mp3"
    output_file_path = os.path.join(settings.MEDIA_ROOT, output_file_name)
    combined_audio.export(output_file_path, format='mp3')
    
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        for subevent_name in file_paths:
            for file_path in file_paths[subevent_name]:
                if not file_path.endswith(".mp3"):
                    file_path = file_path.lstrip("\\")
                    file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    file_name = os.path.basename(file_path)
                    zip_file.write(file_path, arcname=os.path.join(subevent_name, file_name))
        zip_file.write(output_file_path, arcname=output_file_name)

    return zip_file_url

