class Node:
    """Represents a 4-ary tree, used to dispatch sites in distinct zones.

    The partitioning is done when the latitudinal length of the covered zone is greater than
    0.5 OR the longitudinal length is greater than 3.

    This class can be also considered as a node, as its corresponding sites are stored in a list,
    which is a member of this class.
    """

  #  {"id": id_count, "lat": min_lat, "lng": min_lng, "dlat": max_lat - min_lat, "dlng": 0, "zone": [], "points": []}
    def __init__(self,min_lat,min_lng,dlat,dlng,list):
        """Class constructor.
        Parameters:
            min_lat: minimum latitude of the zone.
            min_lng: minimum longitude of the zone.
            dlat: latitudinal length of the zone.
            dlng: longitudinal length of the zone.
            list: sites list.
        """
        self.north_W = None
        self.north_E = None
        self.south_W = None
        self.south_E = None
        self.min_lat = min_lat
        self.min_lng= min_lng
        self.dlat= dlat
        self.dlng = dlng
        self.list=list

    def insert(self):
        """Partitions node sites in sub-zones.

        The partition can be longitudinal if the longitudinal length of the covered zone is greater than 3,
        and / or can be latitudinal if the latitudinal length of the covered zone is greater than 0.5
        """

        # Compare the new value with the parent node
        if self.dlat> 0.5:  # Latitudinal dispatch.
           if self.dlng > 3:    # Latitudinal and longitudinal dispatch.
                self.north_W = Node(self.min_lat + self.dlat/2.0 ,self.min_lng,self.dlat/2.0,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat + self.dlat/2.0 ,self.min_lng,self.dlat/2.0,self.dlng/2.0,
                                                    self.list))
                self.north_E = Node(self.min_lat + self.dlat/2.0,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat + self.dlat/2.0,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,
                                                    self.dlng/2.0,self.list))
                self.south_W = Node(self.min_lat,self.min_lng,self.dlat/2.0,self.dlng/2.0,self.findArrayOfNode(self.min_lat,
                                                                self.min_lng,self.dlat/2.0,self.dlng/2.0,self.list))
                self.south_E = Node(self.min_lat,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,self.dlng/2.0,self.list))
           else:
               self.north_W = Node(self.min_lat + self.dlat/2.0, self.min_lng, self.dlat / 2.0, self.dlng,
                                   self.findArrayOfNode(self.min_lat + self.dlat/2.0, self.min_lng, self.dlat / 2.0,
                                                   self.dlng, self.list))
               self.south_W = Node(self.min_lat, self.min_lng, self.dlat/2.0, self.dlng,
                                   self.findArrayOfNode(self.min_lat, self.min_lng, self.dlat/2.0, self.dlng,self.list))
        else:
           if self.dlng > 0.25:
                self.north_W = Node(self.min_lat ,self.min_lng,self.dlat,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat ,self.min_lng,self.dlat,self.dlng/2.0, self.list))
                self.north_E = Node(self.min_lat ,self.min_lng + self.dlng/2.0, self.dlat, self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat ,self.min_lng + self.dlng/2.0, self.dlat, self.dlng/2.0, self.list))
           else:
               self.north_W = None
               self.north_E = None
               self.south_W = None
               self.south_E = None

        # Recursively partitionning subtrees.
        if self.north_W is not None:
            self.north_W.insert()
        if self.north_E is not None:
            self.north_E.insert()
        if self.south_W is not None:
            self.south_W.insert()
        if self.south_E is not None:
            self.south_E.insert()

    def findArrayOfNode(self,min_lat,min_lng,dlat,dlng, listItem):
        """Finds sites which belongs to a zone of coordinates and size given.
        Parameters:
            min_lat: minimum latitude of the zone.
            min_lng: minimum longitude of the zone.
            dlat: latitudinal length of the zone.
            dlng: longitudinal length of the zone.
        Returns:
            A list of sites which belongs the given zone.
        """
        list=[]
        if len(listItem)!=0:
            for item in listItem:
                if (item["Latitude"] - min_lat <= dlat)&(item["Longitude"]- min_lng<=dlng):
                    list.append(item)
        return list

    def PrintTree(self):
        """Prints the tree."""
        if self.north_W:
            self.north_W.PrintTree()
        if self.north_E:
            self.north_E.PrintTree()
        if self.south_W:
            self.south_W.PrintTree()
        if self.south_E:
            self.south_E.PrintTree()
        # if ((self.north_W == None) & (self.north_E == None) &(self.south_W == None)&(self.south_E == None)):
        print({(self.min_lat, self.min_lng, self.dlat, self.dlng)})


    def PreorderTraversal(self,root):
        """Produces a list of zones by doing a recursive preorder traversal of a tree.
        Parameters:
            root: tree to explore.
        Returns:
            The list of sites found during the traversal.
        """
        res=[]
        if root:
           # if bool(root.min_lat)==False:
            a= {"lat": str(root.min_lat), "lng": str(root.min_lng), "dlat": str(root.dlat),"arrayPoint": root.list,"dlng": str(root.dlng), "zone":
                [self.PreorderTraversal(root.north_W),
                 self.PreorderTraversal(root.north_E),
                 self.PreorderTraversal(root.south_W),
                 self.PreorderTraversal(root.south_E)]}

            a["zone"] = [i for i in a["zone"] if i]
            res.append(a)
        return res



# root = Node(0,0,2,1,[])
# root.insert()
# #print(root.PreorderTraversal(root))
# print(root.PreorderTraversal(root)[0])


