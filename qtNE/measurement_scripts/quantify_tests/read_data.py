import h5py
# filename = "file.hdf5"
filename= "C:\\qtNE_standalone\\measurement_scripts\\quantify_tests\\quantify-data\\20210413\\20210413-103119-951-beb24e-my experiment\\dataset.hdf5"

with h5py.File(filename, "r") as f:
    # List all groups
    print("Keys: %s" % f.keys())
    a_group_key = list(f.keys())[0]

    # Get the data
    data = list(f[a_group_key])
    
print(data)