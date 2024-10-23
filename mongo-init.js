rs.initiate({
    _id: "rs0",
    members: [{ _id: 0, host: "mongo:27017" }]
  });
  
  // Wait for the primary node to be elected
  var primary = rs.status();
  while (primary.members[0].stateStr !== "PRIMARY") {
    sleep(1000);
    primary = rs.status();
  }
  
  // Print a message to confirm the replica set was initialized
  print("Replica set initialized.");
  