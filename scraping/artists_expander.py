import pandas as pd

artists_df = pd.read_csv("FilesCSVFormat/Artist.csv")
specialisation_df = pd.read_csv("FilesCSVFormat/specialization.csv")
movement_df = pd.read_csv("FilesCSVFormat/Movement.csv")
academy_df = pd.read_csv("FilesCSVFormat/Academy.csv")
artist_specialisation_df = pd.read_csv("FilesCSVFormat/ArtistSpecializations.csv")
artist_academy_df = pd.read_csv("FilesCSVFormat/ArtistEducation.csv")
artist_movement_df = pd.read_csv("FilesCSVFormat/ArtistMovements.csv")
apprenticeship_df = pd.read_csv("FilesCSVFormat/Apprenticeship.csv")

# Add specialty to artists
artists_df["specialty"] = None
indices = artist_specialisation_df.index.values.astype(int)
for index in indices:
    artist_id = artist_specialisation_df.artist_id.iloc[index].astype(int)
    speciality_id = artist_specialisation_df.specialty_id.iloc[index].astype(int)
    if artists_df.specialty.iloc[artist_id] is None:
        artists_df.specialty.iloc[artist_id] = [specialisation_df.name.iloc[speciality_id]]
    else:
        artists_df.specialty.iloc[artist_id].append(specialisation_df.name.iloc[speciality_id])

# Add movement to artists
artists_df["movement"] = None
indices = artist_movement_df.index.values.astype(int)
for index in indices:
    artist_id = artist_movement_df.artist_id.iloc[index].astype(int)
    movement_id = artist_movement_df.movement_id.iloc[index].astype(int)
    artists_df.movement.iloc[artist_id] = movement_df.name.iloc[movement_id]
    
#Add academy to artists
artists_df["academy"] = None
indices = artist_academy_df.index.values.astype(int)
for index in indices:
    artist_id = artist_academy_df.artist_id.iloc[index].astype(int)
    academy_id = artist_academy_df.academy_id.iloc[index].astype(int)
    artists_df.academy.iloc[artist_id] = academy_df.name.iloc[academy_id]
    
#Add teaching to artists
artists_df["teacher_of"] = None
artists_df["student_of"] = None
indices = apprenticeship_df.index.values.astype(int)
for index in indices:
    teacher_id = apprenticeship_df.teacher_id.iloc[index].astype(int)
    student_id = apprenticeship_df.student_id.iloc[index].astype(int)
    if artists_df.teacher_of.iloc[teacher_id] is None:
        artists_df.teacher_of.iloc[teacher_id] = [artists_df.name.iloc[student_id]]
    else:
        artists_df.teacher_of.iloc[teacher_id] = [artists_df.name.iloc[student_id]]
    if artists_df.student_of.iloc[student_id] is None:
        artists_df.student_of.iloc[student_id] = [artists_df.name.iloc[teacher_id]]
    else:
        artists_df.student_of.iloc[student_id].append(artists_df.name.iloc[teacher_id])

artists_df.to_csv("artists_expanded.csv", index=None)